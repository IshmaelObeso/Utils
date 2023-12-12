"""
File: zip_directories.py
Author: Ishmael Obeso

Description:
    This script provides functionality to archive directories using the shutil library.
    It supports archiving multiple source directories into the specified output directory,
    with options for different archive formats, overwriting existing archives, and deleting
    source directories after archiving.

Usage:
    python zip_directories.py --source_directories [dir1] [dir2] ... --output_directory [output_dir]
                             --archive_format format --overwrite --delete_source

    Example:
    python zip_directories.py --source_directories /path/to/source1 /path/to/source2
                             --output_directory /path/to/output --archive_format zip --overwrite --delete_source
"""
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
    ZIP = "zip"
    TAR = "tar"
    GZTAR = "tar.gz"
    BZTAR = "tar.bz2"
    XZTAR = "tar.xz"

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

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """

    p = argparse.ArgumentParser()
    p.add_argument('--source_directories', '-s', nargs='+', help='source directories to archive', required=True)
    p.add_argument('--output_directory', required=True, help="directory to output archives")
    p.add_argument('--archive_format', default='bztar', help="format of the archive (e.g., 'zip', 'tar', 'gztar', 'bztar', 'xztar')")
    p.add_argument('--overwrite', '-o', action='store_true', help='whether to overwrite an existing archive')
    p.add_argument('--delete_source', '-d', action='store_true', help='whether to delete source directories after archiving')

    args = p.parse_args()

    archive_format_arg_str = args.archive_format.upper()

    try:
        args.archive_format = ArchiveFormat[archive_format_arg_str]

    except KeyError:
        raise ValueError(f"Invalid archive format: {args.archive_format}")

    return args


def setup_logger(output_directory: Union[str, Path]) -> logging.Logger:
    """
    Set up the logger for the script.

    Args:
        output_directory (str): The directory to output log files.

    Returns:
        logging.Logger: The logger object.
    """

    # Set up logger
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # set up where to output log files to
    log_file_name = f"compression_log_{current_datetime}.txt"

    # define directory to output log files, and create if it doesn't exist
    log_files_dir = Path(output_directory, 'logs')
    log_files_dir.mkdir(parents=True, exist_ok=True)

    log_filepath = Path(log_files_dir, log_file_name)

    # Create a logger object
    logger = logging.getLogger(__name__)

    # set up logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            # Add a FileHandler to log to a file in the output directory
            logging.FileHandler(log_filepath)
        ],
    )

    # # print log file location
    logging.info(f'Log file output to: {log_filepath}')

    return logger


def archive_directory(
        source_directory: Union[str, pathlib.Path],
        archive_path: Union[str, pathlib.Path],
        root_dir: Union[str, pathlib.Path],
        base_dir: Union[str, pathlib.Path],
        archive_format: ArchiveFormat,
        logger: logging.Logger,
        delete: bool,
) -> None:
    """
    Archives a source directory into the specified archive file.

    Args:
        source_directory (Union[str, pathlib.Path]): The path to the source directory to be archived.
        archive_path (Union[str, pathlib.Path]): The path to the archive file to be created.
        root_dir (Union[str, pathlib.Path]): The root directory for the archive.
        base_dir (Union[str, pathlib.Path]): The base directory within the archive.
        archive_format (ArchiveFormat): The format of the archive (e.g., ArchiveFormat.ZIP, ArchiveFormat.TAR).
        logger (logging.Logger): The logger object to handle log messages.
        delete (bool): Flag indicating whether to delete the source directory after archiving.

    Returns:
        None: The function does not return any value.

    Raises:
        Exception: If an error occurs during the archiving process, it is caught and logged.

    Example:
        archive_directory("/path/to/source", "/path/to/archive", "/path/to/root", "base_dir", ArchiveFormat.ZIP, logger, True)
    """

    try:
        # Log the start of the archiving process
        logging.info(f'Starting archive creation from source directory: {source_directory}')

        # get the size of the source directory
        directory_size = get_folder_size(source_directory)

        # if there was no error during calculating source directory size, print it out
        if directory_size:
            # print the size of the original directory
            logging.info(f'Original Directory Size: {directory_size:.2f}')

        # Convert the ArchiveFormat enum back to a string
        archive_format_str = archive_format.name.lower()

        # Create the archive
        shutil.make_archive(archive_path, archive_format_str, root_dir, base_dir, logger=logger)

        # Log the completion of the archiving process
        logging.info(f'Archive created at: {archive_path}')

        # get the size of the compressed archive
        archive_size = get_file_size(archive_path)

        # if there was no error calculating archive size, print it out
        if archive_size:

            # get the size of the archive file
            logging.info(f'Archive Size: {archive_size:.2f}')

            # print out the compression ratio
            logging.info(f'Compression Ratio: {(directory_size/archive_size):.2f}')

        # if we are deleting source after archiving, say so and do it
        if delete:

            # log delete
            logging.info(f'Deleting Source Directory: {source_directory}')

            # delete source dir
            shutil.rmtree(source_directory)

    except Exception as e:
        # log any errors during archiving
        logger.error(f"An error occurred during archiving: {str(e)}")

    return None


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


def get_folder_size(folder_path):
    """
    Get the total size of all files in a directory.

    Args:
        folder_path (str): Path to the directory.

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


def get_file_size(file_path):
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


def main(
        source_directories: List[str],
        output_directory: str,
        archive_format: ArchiveFormat,
        overwrite: bool,
        delete_source: bool,
) -> None:
    """
    The main entry point for the script.

    Args:
        source_directories (List[str]): List of source directories to archive.
        output_directory (str): Directory to output archives.
        archive_format (ArchiveFormat): Archive format (ZIP, TAR, GZTAR, BZTAR, XZTAR).
        overwrite (bool): Flag indicating whether to overwrite existing archives.
        delete_source (bool): Flag indicating whether to delete source directories after archiving.

    Returns:
        None
    """

    start_time = time.time()

    logger = setup_logger(output_directory)

    # check if output dir exists, if not create it
    output_directory = Path(output_directory)

    if output_directory.is_dir():
        # Log output directory exists
        logging.info(f'Output Directory Exists at: {output_directory}')

    else:
        output_directory.mkdir(parents=True, exist_ok=True)
        # Log create output directory
        logging.info(f'Output Directory created at: {output_directory}')

    # Log the amount of directories to archive
    logging.info(f'Archiving: {len(source_directories)} directories')

    if args.overwrite:
        # Log whether we will overwrite archives or not
        logger.warning(f'Overwriting existing archives: {overwrite}')

    if args.delete_source:
        # log whether we will delete source directories after archiging
        logging.warning(f'Deleting source directories after archiving: {delete_source}')

    for source_directory in source_directories:

        # Specify the base name for the archive (excluding the extension)
        archive_base_name = Path(source_directory).stem

        # Full path for the archive file minus the extension
        archive_path = Path(output_directory, archive_base_name)

        # root directory
        root_dir = Path(source_directory).parent
        # base directory
        base_dir = Path(source_directory).stem

        # if we are not overwriting, check if archive file exists, if it does, skip
        if not overwrite:

            archive_filepath = Path(output_directory, f'{archive_base_name}.{archive_format}')

            # if the archive already exists, skip it
            if archive_filepath.is_file():

                # log that we skip
                logging.info(f'{source_directory} Archive already exists at {archive_filepath}, Skipping...')
                pass

            else:
                archive_directory(
                    source_directory,
                    archive_path,
                    root_dir,
                    base_dir,
                    archive_format,
                    logger,
                    delete_source
                )

        # else if we are overwriting, then archive every file
        else:
            archive_directory(
                source_directory,
                archive_path,
                root_dir,
                base_dir,
                archive_format,
                logger,
                delete_source
            )

    end_time = time.time()
    total_time = end_time - start_time

    # Log script completion, including total number of archives created
    logging.info(f'Archiving Directories Finished! Total Archives Created: {len(source_directories)}')
    logging.info(f'Total Time Elapsed: {get_time_hh_mm_ss(total_time)}')


if __name__ == "__main__":

    # get cmd line arguments
    args = parse_arguments()

    # get the cmd line args
    source_directories = args.source_directories
    output_directory = args.output_directory
    archive_format = args.archive_format
    overwrite = args.overwrite
    delete_source = args.delete_source

    # run main function
    main(
        source_directories=source_directories,
        output_directory=output_directory,
        archive_format=archive_format,
        overwrite=overwrite,
        delete_source=delete_source,
    )
