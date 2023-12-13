import pathlib
import shutil
import logging
import argparse
import time
from datetime import timedelta, datetime
from pathlib import Path
from typing import Union, List
from enum import Enum

class ArchiveFormat(Enum):
    """
    Enumeration representing different archive formats.

    This enum defines the supported archive formats for use in the script. Each format is associated
    with a string value that corresponds to commonly used archive file extensions.

    Supported Formats:
        - ZIP: ZIP archive format.
        - TAR: TAR archive format.
        - GZTAR: GZipped TAR archive format.
        - BZTAR: BZipped TAR archive format.
        - XZTAR: XZipped TAR archive format.

    Example:
        To use an archive format in the script, you can reference the enum values like this:

        ```python
        format = ArchiveFormat.ZIP
        ```

    Attributes:
        ZIP (str): String value representing the ZIP archive format.
        TAR (str): String value representing the TAR archive format.
        GZTAR (str): String value representing the GZipped TAR archive format.
        BZTAR (str): String value representing the BZipped TAR archive format.
        XZTAR (str): String value representing the XZipped TAR archive format.
    """
    ZIP = "zip"
    TAR = "tar"
    GZTAR = "tar.gz"
    BZTAR = "tar.bz2"
    XZTAR = "tar.xz"

class ArchiveSuffixes(Enum):

    SUFFIXES = {'.zip', '.tar', '.gz', '.bz2', '.xz'}


class ByteSize(int):
    """
    Represents a byte size with additional properties for kilobytes, megabytes, gigabytes, and petabytes.

    Attributes:
        bytes (int): Size in bytes.
        kilobytes (float): Size in kilobytes.
        megabytes (float): Size in megabytes.
        gigabytes (float): Size in gigabytes.
        petabytes (float): Size in petabytes.
    """
    _KB = 1024
    _suffixes = 'B', 'KB', 'MB', 'GB', 'PB'

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.bytes = self.B = int(self)
        self.kilobytes = self.KB = self / self._KB ** 1
        self.megabytes = self.MB = self / self._KB ** 2
        self.gigabytes = self.GB = self / self._KB ** 3
        self.petabytes = self.PB = self / self._KB ** 4
        *suffixes, last = self._suffixes
        suffix = next((
            suffix
            for suffix in suffixes
            if 1 < getattr(self, suffix) < self._KB
        ), last)
        self.readable = suffix, getattr(self, suffix)

        super().__init__()

    def __str__(self):
        return self.__format__('.2f')

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, super().__repr__())

    def __format__(self, format_spec):
        suffix, val = self.readable
        return '{val:{fmt}} {suf}'.format(val=val, fmt=format_spec, suf=suffix)

    def __sub__(self, other):
        return self.__class__(super().__sub__(other))

    def __add__(self, other):
        return self.__class__(super().__add__(other))

    def __mul__(self, other):
        return self.__class__(super().__mul__(other))

    def __rsub__(self, other):
        return self.__class__(super().__sub__(other))

    def __radd__(self, other):
        return self.__class__(super().__add__(other))

    def __rmul__(self, other):
        return self.__class__(super().__rmul__(other))


def get_folder_size(folder_path: Union[str, Path]) -> ByteSize:
    """
    Get the total size of all files in a directory.

    Args:
        folder_path (str: path): Path to the directory.

    Returns:
        ByteSize: Total size of all files in bytes.
    """

    folder = Path(folder_path)

    # Check if the path is a directory
    if not folder.is_dir():
        raise ValueError(f"{folder_path} is not a directory.")

    # Get the total size of all files in the directory
    try:
        total_size = ByteSize(sum(f.stat().st_size for f in folder.glob('**/*') if f.is_file()))
    except Exception as e:
        logging.error(f"Non-critical error: {str(e)}")
        total_size = None

    return total_size


def get_file_size(file_path: Union[str, Path]) -> ByteSize:
    """
    Get the size of a file.

    Args:
        file_path (str): Path to the file.

    Returns:
        ByteSize: Size of the file in bytes.
    """

    file = Path(file_path)

    # Check if the path is a file
    if not file.is_file():
        raise ValueError(f"{file_path} is not a File.")

    # Get the size of the file
    try:
        file_size = ByteSize(file.stat().st_size)
    except Exception as e:
        logging.error(f"Non-critical error: {str(e)}")
        file_size = None

    return file_size

def get_time_hh_mm_ss(sec: Union[int, float]) -> str:
    """
    Converts a given number of seconds into a formatted string representing hours, minutes, and seconds.

    Parameters:
        sec (int, float): The total number of seconds to be converted.

    Returns:
        str: A string representing the time in the format 'H Hours, M Minutes, S Seconds'.
    """

    # create timedelta and convert it into string
    td_str = str(timedelta(seconds=sec))

    # split string into individual component
    time_split_string = td_str.split(':')

    time_string = f'{time_split_string[0]} Hours, {time_split_string[1]} Minutes, {time_split_string[2]} Seconds'

    return time_string


def setup_logger(output_directory: Union[str, Path], log_level: int = logging.WARNING, log_type: str = None) -> logging.Logger:
    """
    Set up the logger for the script.

    Args:
        output_directory (Union[str, Path]): The directory to output log files.
        log_level (int): The logging severity level to set. Should be one defined in the logging module
                        (e.g., logging.DEBUG, logging.INFO)
        log_type (str, optional): A type identifier for the log. Defaults to None.

    Returns:
        logging.Logger: The logger object.
    """

    # Set up logger
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if log_type:
        # set up where to output log files to
        log_file_name = f"{log_type}_log_{current_datetime}.txt"
    else:
        # set up where to output log files to
        log_file_name = f"log_{current_datetime}.txt"

    # define directory to output log files, and create if it doesn't exist
    log_files_dir = Path(output_directory, 'logs')

    # check if log dir exists, if not, make it
    if not log_files_dir.is_dir():
        log_files_dir.mkdir(parents=True, exist_ok=True)

    log_filepath = Path(log_files_dir, log_file_name)

    # Create a logger object
    logger = logging.getLogger(__name__)

    # set up logger
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            # Add a FileHandler to log to a file in the output directory
            logging.FileHandler(log_filepath)
        ],
    )

    # set log level seperately from the logger instantiation, so it works properly
    logging.getLogger().setLevel(log_level)

    # # print log file location
    logging.info(f'Log file output to: {log_filepath}')

    return logger

def remove_suffixes(path: Path, suffixes_to_remove: List[str]) -> Path:
    """
    Removes specified suffixes from a pathlib.Path object

    Args:
    - path (Path): The pathlib.Path object
    - suffixes_to_remove (list): List of suffixes to be removed

    Returns:
    - Path: the modified pathlib.Path object

    """

    # remove extension suffixes
    for suffix in suffixes_to_remove:
        path = path.with_suffix(path.suffix.removesuffix(suffix))

    return path


def get_base_directory(source_file: Union[str, Path]) -> Path:
    """
    Get the base directory path from the source file path.

    Args:
        source_file (str): The path to the source archive file.

    Returns:
        Path: The path to the base directory.
    """
    # the path the source archive file
    source_file = Path(source_file)

    # get the archive directory suffixes
    unpacked_archive_directory_suffixes = source_file.suffixes
    # reverse their order to they are removed from right to left
    unpacked_archive_directory_suffixes.reverse()
    # Preserve the order of suffixes when getting the intersection
    archive_suffixes_to_remove = [suffix for suffix in unpacked_archive_directory_suffixes if suffix in ArchiveSuffixes.SUFFIXES.value]

    # Remove suffixes from archive directory name
    path = remove_suffixes(source_file, archive_suffixes_to_remove)

    return path