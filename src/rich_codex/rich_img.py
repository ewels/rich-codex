import difflib
import json
import logging
import os
import re
import signal
import subprocess
from pathlib import Path
from shutil import copyfile
from tempfile import gettempdir, mkstemp

import rich.terminal_theme
import yaml
from Levenshtein import ratio
from rich.ansi import AnsiDecoder
from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax

log = logging.getLogger("rich-codex")

# Parse the config schema file to get config attributes
config_schema_fn = Path(__file__).parent / "config-schema.yml"
with config_schema_fn.open() as fh:
    config_schema = yaml.safe_load(fh)
RICH_IMG_ATTRS = config_schema["properties"]["outputs"]["items"]["properties"].keys()

# Base list of commands to ignore
IGNORE_COMMANDS = ["rm", "cp", "mv", "sudo"]

# Base list of diff regexes to ignore, split up by filetype suffix
IGNORE_REGEXES = {".pdf": [r"/CreationDate"]}


class RichImg:
    """Image generation for rich-codex.

    Objects from this class are typically used once per screenshot.
    """

    def __init__(
        self,
        command=None,
        working_dir=None,
        snippet=None,
        img_paths=None,
        snippet_syntax=None,
        timeout=5,
        before_command=None,
        after_command=None,
        title=None,
        fake_command=None,
        hide_command=False,
        title_command=False,
        extra_env=None,
        head=None,
        tail=None,
        trim_after=None,
        truncated_text="[..truncated..]",
        min_pct_diff=0,
        skip_change_regex=None,
        terminal_width=None,
        terminal_min_width=80,
        notrim=False,
        terminal_theme=None,
        snippet_theme=None,
        use_pty=False,
        console=None,
        source_type=None,
        source=None,
    ):
        """Initialise the RichImg object with core console options."""
        self.command = command
        self.working_dir = Path.cwd() if working_dir is None else working_dir
        self.snippet = snippet
        self.img_paths = [] if img_paths is None else img_paths
        self.snippet_syntax = snippet_syntax
        self.timeout = timeout
        self.before_command = before_command
        self.after_command = after_command
        self.title = "" if title is None else title
        self.fake_command = fake_command
        self.hide_command = hide_command
        self.title_command = title_command
        self.extra_env = {} if extra_env is None else extra_env
        self.head = None if head is None else int(head)
        self.tail = None if tail is None else int(tail)
        self.trim_after = trim_after
        self.truncated_text = truncated_text
        self.min_pct_diff = min_pct_diff
        self.skip_change_regex = skip_change_regex
        self.terminal_width = None if terminal_width is None else int(terminal_width)
        self.terminal_min_width = None if terminal_min_width is None else int(terminal_min_width)
        if self.terminal_width and self.terminal_min_width and self.terminal_min_width > self.terminal_width:
            self.terminal_min_width = None
        self.notrim = notrim
        self.terminal_theme = terminal_theme
        self.snippet_theme = snippet_theme
        self.use_pty = use_pty
        self.console = Console() if console is None else console
        self.capture_console = None
        self.saved_img_paths = []
        self.num_img_saved = 0
        self.num_img_skipped = 0
        self.no_confirm = False
        self.aborted = False
        self.source_type = source_type
        self.source = source

    def __eq__(self, other):
        """Compare RichImg objects for equality."""
        if not isinstance(other, RichImg):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return all(getattr(self, attr) == getattr(other, attr) for attr in RICH_IMG_ATTRS)

    def __hash__(self):
        """Hash stable identifier of RichImg object based on important attributes."""
        attrs = str([getattr(self, attr) for attr in RICH_IMG_ATTRS])
        return hash(attrs)

    def _hash_no_fn(self):
        """Hash stable identifier of RichImg object based without output filenames."""
        attrs = str([getattr(self, attr) for attr in RICH_IMG_ATTRS if attr != "img_paths"])
        return hash(attrs)

    def confirm_command(self):
        """Prompt user to confirm running command."""
        if self.command is None or self.no_confirm:
            return True
        return Confirm.ask(f"Command: [white on black] {self.command} [/] Run?", console=self.console)

    def run_command(self):
        """Capture output from a supplied command and save to an image."""
        if self.command is None:
            log.debug("Tried to generate image with no command")
            return

        self.command = self.command.strip()

        for ignore in IGNORE_COMMANDS:
            if any(cmd_part.strip().startswith(ignore) for cmd_part in self.command.split("&;")):
                log.warning(f"Ignoring command because it contained '{ignore}': [white on black] {self.command} [/]")
                self.aborted = True
                return False

        if self.title == "" and self.title_command:
            self.title = self.fake_command if self.fake_command else self.command

        if self.use_pty:
            log.debug(f"Running command '{self.command}' with pty")

            try:
                import fcntl
                import pty
                import struct
                import termios

                run_with_pty = True
            except ImportError:
                # fallback method needed
                log.warning(
                    "Could not use pty, import failed (are you using Windows? pty is not usable there). "
                    "Falling back to subprocess."
                )
                run_with_pty = False
        else:
            log.debug(f"Running command '{self.command}' with subprocess")
            run_with_pty = False

        # Create working directory if it doesn't already exist
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Set up the command environment vars, with extra_env if set
        command_env = os.environ.copy()
        if len(self.extra_env):
            log.debug(f"Adding extra env variables: {self.extra_env}")
            command_env.update({str(k): str(v) for k, v in self.extra_env.items()})

        # Run before_command if set
        if self.before_command:
            log.debug("Running 'before_command'")
            # TODO: Can't get inspect() to output to a log call
            # NOTE: https://github.com/Textualize/rich/discussions/2378
            # log.debug(
            #     inspect(
            subprocess.run(
                self.before_command,
                cwd=self.working_dir,
                shell=True,
                env=command_env,
                capture_output=True,
            )
            #         , title="'before_command' results",
            #         docs=False,
            #     )
            # )

        # Run the command with a fake tty to try to get colours
        if run_with_pty:
            read_end, write_end = pty.openpty()

            # Resize routine for pty
            # First, get our own current terminal size
            # (struct is documented here: https://www.delorie.com/djgpp/doc/libc/libc_495.html)
            size = fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))

            # Rewrite size with selected terminal width if set
            if self.terminal_width is not None:
                data = struct.unpack("HHHH", size)
                size = struct.pack("HHHH", data[0], self.terminal_width, 0, 0)

            # Issue command to pty to resize
            fcntl.ioctl(write_end, termios.TIOCSWINSZ, size)
            fcntl.ioctl(read_end, termios.TIOCSWINSZ, size)
            signal.signal(signal.SIGWINCH, lambda s, f: fcntl.ioctl(write_end, termios.TIOCSWINSZ, size))
            signal.signal(signal.SIGWINCH, lambda s, f: fcntl.ioctl(read_end, termios.TIOCSWINSZ, size))

            # Run subprocess in pty
            try:
                process = subprocess.Popen(
                    self.command,
                    cwd=self.working_dir,
                    shell=True,
                    env=command_env,
                    close_fds=True,
                    preexec_fn=os.setsid,
                    stdin=write_end,
                    stdout=write_end,
                    stderr=write_end,
                )
                process.wait(timeout=float(self.timeout))
            except subprocess.TimeoutExpired:
                log.info(f"Command '{self.command}' timed out after {self.timeout} seconds")
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            os.close(write_end)

            output_arr = []

            # This loop will keep going until no more data is incoming (child process closed their pipe)
            while True:
                try:
                    data = os.read(read_end, 1024)
                except OSError:
                    data = b""

                if data:
                    output_arr.append(data)
                else:
                    break

            os.close(read_end)
            output = b"".join(output_arr).decode("utf-8")

        # Run the command without messing with ttys
        else:
            try:
                process = subprocess.Popen(
                    self.command,
                    cwd=self.working_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,  # Needed for pipes
                    env=command_env,
                    start_new_session=True,  # Needed for subprocess termination
                )
                output, errs = process.communicate(timeout=float(self.timeout))
            except subprocess.TimeoutExpired:
                log.info(f"Command '{self.command}' timed out after {self.timeout} seconds")
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                output, errs = process.communicate()
            output = output.decode("utf-8")

        # Run after_command if set
        if self.after_command:
            log.debug("Running 'after_command'")
            # TODO: Can't get inspect() to output to a log call
            # NOTE: https://github.com/Textualize/rich/discussions/2378
            # log.debug(
            #     inspect(
            subprocess.run(
                self.after_command,
                cwd=self.working_dir,
                shell=True,
                env=command_env,
                capture_output=True,
            )
            #         , title="'after_command' results",
            #         docs=False,
            #     )
            # )

        decoder = AnsiDecoder()

        # Count lines and find longest line
        print_lines = []
        max_line_length = 0
        for line in decoder.decode(output):
            print_lines.append(True)
            max_line_length = max(len(line), max_line_length)

        # If terminal_min_width is set, find longest line
        t_width = int(self.terminal_width) if self.terminal_width else None
        if not self.notrim and self.terminal_min_width:
            t_width = int(self.terminal_min_width)
            t_width = max(t_width, max_line_length)
            log.debug(f"Setting terminal width to {t_width}")
        self.capture_console = Console(
            file=open(os.devnull, "w"),
            force_terminal=True,
            color_system="truecolor",
            highlight=False,
            record=True,
            width=t_width,
        )

        # Set head / tail print set
        if self.head and self.head >= len(print_lines):
            self.head = None
        if self.tail and self.tail >= len(print_lines):
            self.tail = None
        if self.head is not None or self.tail is not None:
            print_lines = [False] * len(print_lines)
            if self.head is not None:
                print_lines[: self.head] = [True] * self.head
            if self.tail is not None:
                print_lines[len(print_lines) - self.tail :] = [True] * self.tail

        # Print the command
        if not self.hide_command:
            self.capture_console.print(
                "$ {}".format(
                    self.fake_command if self.fake_command else self.command,
                )
            )

        # Decode and print the output (captured)
        for idx, line in enumerate(decoder.decode(output)):
            if print_lines[idx]:
                self.capture_console.print(line)
                # Trim text after trim_after
                if self.trim_after and self.trim_after in line:
                    break
            elif (self.head is not None or self.tail is not None) and self.truncated_text:
                self.capture_console.print(self.truncated_text, style="italic dim")
                self.truncated_text = None

    def format_snippet(self):
        """Take a text snippet and format it using rich."""
        if self.snippet is None:
            log.debug("Tried to format snippet with no snippet")
            return

        # Reformat JSON with pretty printing, because we can
        if self.snippet_syntax == "json" or self.snippet_syntax is None:
            try:
                json_snippet = json.loads(self.snippet)
                self.snippet = json.dumps(json_snippet, indent=4, sort_keys=True)
                self.snippet_syntax = "json"
            except json.decoder.JSONDecodeError:
                pass

        # Adjust terminal width if min-width set
        t_width = int(self.terminal_width) if self.terminal_width else None
        if not self.notrim and self.terminal_min_width:
            t_width = int(self.terminal_min_width)
            for line in self.snippet.splitlines():
                t_width = max(len(line), t_width)
            log.debug(f"Setting terminal width to {t_width}")

        self.capture_console = Console(
            file=open(os.devnull, "w"),
            force_terminal=True,
            color_system="truecolor",
            highlight=False,
            record=True,
            width=t_width,
        )

        # Print with rich Syntax highlighter
        log.debug(f"Formatting snippet as {self.snippet_syntax}")
        snippet_theme = "monokai" if self.snippet_theme is None else self.snippet_theme  # Same default as Rich
        syntax = Syntax(self.snippet, self.snippet_syntax, theme=snippet_theme)
        self.capture_console.print(syntax)

    def get_output(self):
        """Either run command or format snippet, depending on what is set."""
        if self.command is not None:
            self.run_command()
        elif self.snippet is not None:
            self.format_snippet()
        else:
            log.warning("Tried to get output with no command or snippet")

    def _enough_image_difference(self, new_fn, old_fn):
        new_file = Path(new_fn)
        old_file = Path(old_fn)
        create_file = True
        log_msg = ""

        # Target file doesn't exist yet, nothing to compare against
        if not old_file.exists():
            log_msg = "new image"

        else:
            # Percentage change in file
            # This method works even with entirely binary files, no decoding required
            pct_change = (1 - ratio(new_file.read_bytes(), old_file.read_bytes())) * 100.0
            if pct_change <= float(self.min_pct_diff):
                create_file = False
            log_msg = f"{pct_change:.2f}% change"

            # No point in looking for a diff if the files are identical
            if pct_change > 0:

                # Regex on file diff to skip
                skip_regexes = list(r for r in IGNORE_REGEXES.get(new_file.suffix, []))  # deep copy
                if self.skip_change_regex:
                    skip_regexes.extend(self.skip_change_regex.splitlines())
                if len(skip_regexes) > 0:
                    new_file_lines = new_file.read_text(errors="ignore").splitlines()
                    old_file_lines = old_file.read_text(errors="ignore").splitlines()
                    log.info("Checking diff")

                    # Only continue if we found something to diff with
                    if len(new_file_lines) > 0 or len(old_file_lines) > 0:
                        log.info("starting..")
                        diffs = difflib.Differ().compare(new_file_lines, old_file_lines)
                        log.info("generated diff ")
                        log.info(f"len: {len(list(diffs))}")
                        lost_lines = [d for d in diffs if d.startswith("-")]

                        # Only continue if there was some diff
                        log.info(f"Found {lost_lines} lines")
                        if len(lost_lines) > 0:
                            matched_lost_lines = []
                            for skip_regex in skip_regexes:
                                for line in lost_lines:
                                    if re.search(skip_regex, line):
                                        matched_lost_lines.append(line)

                            log_msg += f", {len(matched_lost_lines)}/{len(lost_lines)} diff lines matched regex filters"
                            if len(matched_lost_lines) == len(lost_lines):
                                create_file = False
                        else:
                            log_msg += ", no diff found"
                    else:
                        log_msg += ", no text to diff"

        old_fn_relative = old_file.resolve().relative_to(Path.cwd())
        if create_file:
            self.num_img_saved += 1
            self.saved_img_paths.append(old_fn)
            log.info(f"Saved: '{old_fn_relative}' ({log_msg})")
        else:
            self.num_img_skipped += 1
            log.debug(f"[dim]Skipped: '{old_fn_relative}' ({log_msg})")

        return create_file

    def save_images(self):
        """Save the images to the specified filenames."""
        if self.aborted:
            return
        if len(self.img_paths) == 0:
            log.warning("Tried to save images with no paths")
            return

        # Set up theme
        terminal_theme = None
        if self.terminal_theme:
            try:
                terminal_theme = getattr(rich.terminal_theme, self.terminal_theme)
            except AttributeError:
                log.error(
                    "[red]Theme '{}' not found![/] Falling back to default for [magenta]{}".format(
                        self.terminal_theme, ", ".join(self.img_paths)
                    )
                )

        # Save image as requested with $IMG_PATHS
        svg_img = None
        png_img = None
        pdf_img = None
        for filename in self.img_paths:

            # Make directories if necessary
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            # If already made this image, copy it from the last destination
            if filename.lower().endswith(".png") and png_img is not None:
                log.debug(f"Using '{png_img}' for '{filename}'")
                if self._enough_image_difference(png_img, filename):
                    copyfile(png_img, filename)
                continue
            if filename.lower().endswith(".pdf") and pdf_img is not None:
                log.debug(f"Using '{pdf_img}' for '{filename}'")
                if self._enough_image_difference(pdf_img, filename):
                    copyfile(pdf_img, filename)
                continue
            if filename.lower().endswith(".svg") and svg_img is not None:
                log.debug(f"Using '{svg_img}' for '{filename}'")
                if self._enough_image_difference(svg_img, filename):
                    copyfile(svg_img, filename)
                continue

            # Set filenames
            tmp_filename = mkstemp()[1]

            # We always generate an SVG first
            if svg_img is None:
                svg_tmp_filename = mkstemp()[1]
                self.capture_console.save_svg(
                    svg_tmp_filename,
                    title=self.title,
                    theme=terminal_theme,
                )
            else:
                # Use already-generated SVG
                svg_tmp_filename = svg_img

            # Save the SVG image if requested
            if filename.lower().endswith(".svg"):
                if self._enough_image_difference(svg_tmp_filename, filename):
                    copyfile(svg_tmp_filename, filename)
                svg_img = filename

            # Lazy-load PNG / PDF libraries if needed
            if filename.lower().endswith(".png") or filename.lower().endswith(".pdf"):
                try:
                    from cairosvg import svg2pdf, svg2png
                except ImportError as e:
                    log.debug(e)
                    log.error("CairoSVG not installed, cannot convert SVG to PNG or PDF.")
                    log.info("Please install with cairo extra: 'rich-codex[cairo]'")
                    continue
                except OSError as e:
                    log.debug(e)
                    log.error(
                        "⚠️  Missing [link=https://cairosvg.org/documentation/]CairoSVG dependencies[/], "
                        "cannot convert SVG to PNG or PDF. ⚠️\n"
                        f"[red]Skipping image '{filename}'[/]"
                    )
                    continue

                # Convert to PNG if requested
                if filename.lower().endswith(".png"):
                    log.debug(f"Converting SVG '{svg_tmp_filename}' to PNG '{filename}'")
                    svg2png(
                        file_obj=open(svg_tmp_filename, "rb"),
                        write_to=tmp_filename,
                        dpi=300,
                        output_width=4000,
                    )
                    if self._enough_image_difference(tmp_filename, filename):
                        copyfile(tmp_filename, filename)
                        png_img = filename

                # Convert to PDF if requested
                if filename.lower().endswith(".pdf"):
                    log.debug(f"Converting SVG '{svg_tmp_filename}' to PDF '{filename}'")
                    svg2pdf(
                        file_obj=open(svg_tmp_filename, "rb"),
                        write_to=tmp_filename,
                    )
                    if self._enough_image_difference(tmp_filename, filename):
                        copyfile(tmp_filename, filename)
                        pdf_img = filename

            # Delete temprary files
            tmp_path = Path(tmp_filename)
            if tmp_path.is_relative_to(gettempdir()):
                tmp_path.unlink()

        # Delete temporary SVG file - after loop as can be reused
        tmp_svg_path = Path(svg_tmp_filename)
        if tmp_svg_path.is_relative_to(gettempdir()):
            tmp_svg_path.unlink()
