"""
File: compress_directories.py
Author: Ishmael Obeso

Description:
    This script provides functionality to archive directories using the shutil library.
    It supports archiving multiple source directories into the specified output directory,
    with options for different archive formats, overwriting existing archives, and deleting
    source directories after archiving.

Usage:
    python compress_directories.py --source_directories [dir1] [dir2] ... --output_directory [output_dir]
                             --archive_format format --overwrite --delete_source --verbose

    Example:
    python compress_directories.py --source_directories /path/to/source1 /path/to/source2
                             --output_directory /path/to/output --archive_format zip -o -d -v

Command Line Arguments:
    --source_directories, -s: List of source directories to archive.
    --output_directory: Directory to output archives.
    --archive_format: Format of the archive (e.g., 'zip', 'tar', 'gztar', 'bztar', 'xztar').
    --overwrite, -o: Flag indicating whether to overwrite an existing archive.
    --delete_source, -d: Flag indicating whether to delete source directories after archiving.
    --verbose, -v: Verbosity flag to control the level of logging. Default is set to WARNING.

Enums:
    ArchiveFormat: Enum representing different archive formats (ZIP, TAR, GZTAR, BZTAR, XZTAR).

Functions:
    - parse_arguments(): Parses command line arguments using argparse and returns the parsed arguments.
    - archive_directory(source_directory, archive_path, root_dir, base_dir, archive_format, logger, delete):
        Archives a source directory into the specified archive file.
    - main(source_directories, output_directory, archive_format, overwrite, delete_source, log_level):
        Main function to orchestrate the archiving process.

Utilities:
    - Various utility functions such as get_folder_size, get_file_size, get_time_hh_mm_ss, and setup_logger are imported from the 'utils' module.

Execution:
    - When executed as the main script, it parses command line arguments, sets up logging, and calls the main function to initiate the archiving process.

Example:
    python compress_directories.py --source_directories /path/to/source --output_directory /path/to/output
                             --archive_format zip --overwrite --delete_source
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
from utils import get_folder_size, get_file_size, get_time_hh_mm_ss, setup_logger, ArchiveFormat



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
    p.add_argument(
                   '-v', '--verbose',
                   help='Be verbose',
                   action='store_const',
                   dest='log_level',
                   const=logging.INFO,
        default=logging.WARNING
    )

    args = p.parse_args()

    archive_format_arg_str = args.archive_format.upper()

    try:
        args.archive_format = ArchiveFormat[archive_format_arg_str]

    except KeyError:
        raise ValueError(f"Invalid archive format: {args.archive_format}")

    return args


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

        archive_output_filepath = Path(f'{archive_path}.{archive_format.value}')

        # get the size of the compressed archive
        archive_size = get_file_size(archive_output_filepath)

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


def main(
        source_directories: List[str],
        output_directory: str,
        archive_format: ArchiveFormat,
        overwrite: bool,
        delete_source: bool,
        log_level: int,
) -> None:
    """
    The main entry point for the script.

    Args:
        source_directories (List[str]): List of source directories to archive.
        output_directory (str): Directory to output archives.
        archive_format (ArchiveFormat): Archive format (ZIP, TAR, GZTAR, BZTAR, XZTAR).
        overwrite (bool): Flag indicating whether to overwrite existing archives.
        delete_source (bool): Flag indicating whether to delete source directories after archiving.
        log_level (int): The logging severity level to set. Should be one defined in the logging module
                (e.g., logging.DEBUG, logging.INFO)

    Returns:
        None
    """

    start_time = time.time()

    logger = setup_logger(output_directory, log_level=log_level, log_type='compression')

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

    if overwrite:
        # Log whether we will overwrite archives or not
        logger.info(f'Overwriting existing archives: {overwrite}')

    if delete_source:
        # log whether we will delete source directories after archiging
        logging.info(f'Deleting source directories after archiving: {delete_source}')

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
                # remove from list of source directories
                source_directories.remove(source_directory)

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
    log_level = args.log_level

    # run main function
    main(
        source_directories=source_directories,
        output_directory=output_directory,
        archive_format=archive_format,
        overwrite=overwrite,
        delete_source=delete_source,
        log_level=log_level
    )
