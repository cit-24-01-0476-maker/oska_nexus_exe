"""Unicode diagnostics must never interrupt speech recognition or commands."""
import builtins
import sys


def configure_unicode_streams():
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)
            except (OSError, ValueError, AttributeError):
                # GUI applications and test runners may provide closed/custom streams.
                pass


def safe_print(*values, sep=' ', end='\n', file=None, flush=False):
    stream = file if file is not None else sys.stdout
    if stream is None:
        return
    try:
        builtins.print(*values, sep=sep, end=end, file=stream, flush=flush)
    except UnicodeError:
        # Preserve the actual transcript; escape only its diagnostic representation.
        try:
            text = sep.join(str(value) for value in values) + end
            stream.write(text.encode('ascii', errors='backslashreplace').decode('ascii'))
            if flush:
                stream.flush()
        except (UnicodeError, OSError, ValueError):
            pass
    except (OSError, ValueError):
        pass
