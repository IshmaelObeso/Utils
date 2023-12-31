"""
File: decompress_files.py

Author: Ishmael Obeso

Description:
    This script provides functionality to unpack a list of source archive files into a specified output directory.
    It supports various options such as overwriting existing unpacked archives, deleting source archives after unpacking,
    and configuring the verbosity of logging.

Usage:
    python script_name.py --source_files <source_archive_1> <source_archive_2> ... --output_directory <output_directory>
                          [--overwrite] [--delete_source] [--verbose]

Command Line Arguments:
    --source_files, -s: List of source archive files to unpack.
    --output_directory: Directory to output the unpacked files.
    --overwrite, -o: Flag indicating whether to overwrite existing unpacked archives.
    --delete_source, -d: Flag indicating whether to delete source archives after unpacking.
    --verbose, -v: Verbosity flag to control the level of logging. Default is set to WARNING.

Functions:
    - parse_arguments(): Parses command line arguments using argparse and returns the parsed arguments.
    - unpack_archive(source_file, output_directory, logger, delete): Unpacks a source archive file into the output directory.
    - main(source_files, output_directory, overwrite, delete_source, log_level): Main function to orchestrate the unpacking process.

Logging:
    - The script utilizes the logging module to provide detailed information about the unpacking process.
    - Log messages are written to both the console and log files in the 'logs' directory.

Utilities:
    - Various utility functions such as get_folder_size, get_file_size, get_time_hh_mm_ss, and setup_logger are imported from the 'utils' module.

Execution:
    - When executed as the main script, it parses command line arguments, sets up logging, and calls the main function to initiate the unpacking process.

Example:
    python script_name.py --source_files archive1.zip archive2.tar.gz --output_directory output_folder -o -d -v
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
from utils import get_folder_size, get_file_size, get_time_hh_mm_ss, setup_logger, get_unpacked_archive_directory


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """

    p = argparse.ArgumentParser()
    p.add_argument('--source_files', '-s', nargs='+', help='source archives to unpack', required=True)
    p.add_argument('--output_directory', required=True, help="directory to output unpacked archives")
    p.add_argument('--overwrite', '-o', action='store_true', help='whether to overwrite an existing unpacked archive')
    p.add_argument('--delete_source', '-d', action='store_true', help='whether to delete source archives after unpacking')
    p.add_argument(
                   '-v', '--verbose',
                   help='Be verbose',
                   action='store_const',
                   dest='log_level',
                   const=logging.INFO,
        default=logging.WARNING
    )

    args = p.parse_args()

    return args


def unpack_archive(
        source_file: Union[str, pathlib.Path],
        output_directory: Union[str, pathlib.Path],
        logger: logging.Logger,
        delete: bool,
) -> None:
    """
    Unpacks the given source archive file into the specified output directory.

    Args:
        source_file (Union[str, pathlib.Path]): Path to the source archive file.
        output_directory (Union[str, pathlib.Path]): Directory to output the unpacked files.
        logger (logging.Logger): Logger object for logging messages.
        delete (bool): Whether to delete the source archive file after unpacking.

    Returns:
        None
    """

    try:
        # Log the start of the unpacking process
        logging.info(f'Starting unpacking archive from file: {source_file}')

        # get the size of the archive file
        archive_size = get_file_size(source_file)

        # if there was no error during calculating source archive size, print it out
        if archive_size:
            # print the size of the original directory
            logging.info(f'Original Archive Size: {archive_size:.2f}')

        # # Unpack the archive
        shutil.unpack_archive(source_file, output_directory)

        # Get the directory of the unpacked archive
        unpacked_archive_directory = get_base_directory(source_file)

        # get the whole output archive path
        output_archive_path = Path(output_directory, Path(unpacked_archive_directory).stem)

        # Log the completion of the archiving process
        logging.info(f'Unpacked Archive created at: {output_archive_path}')

        # get the size of the compressed archive
        unpacked_archive_size = get_folder_size(output_archive_path)

        # if there was no error calculating archive size, print it out
        if unpacked_archive_size:

            # get the size of the archive file
            logging.info(f'Unpacked Archive Size: {unpacked_archive_size:.2f}')

            # print out the decompression ratio
            logging.info(f'Decompression Ratio: {(unpacked_archive_size/archive_size):.2f}')

        # if we are deleting source after archiving, say so and do it
        if delete:

            # log delete
            logging.info(f'Deleting Source Archive File: {source_file}')

            # delete source file
            if Path(source_file).is_file():
                shutil.unlink(source_file, missing_ok=True)

    except Exception as e:
        # log any errors during unpacking
        logger.error(f"An error occurred during unpacking: {str(e)}")

    return None


def main(
        source_files: List[str],
        output_directory: Union[str, Path],
        overwrite: bool,
        delete_source: bool,
        log_level: int,
) -> None:
    """
    Main function to unpack archives based on provided command line arguments.

    Args:
        source_files (List[str]): List of source archive files to unpack.
        output_directory (Union[str, Path]): Directory to output the unpacked files.
        overwrite (bool): Whether to overwrite existing unpacked archives.
        delete_source (bool): Whether to delete source archives after unpacking.
        log_level (int): Logging severity level.

    Returns:
        None
    """

    start_time = time.time()

    logger = setup_logger(output_directory, log_level=log_level, log_type='decompression')

    # check if output dir exists, if not create it
    output_directory = Path(output_directory)

    if output_directory.is_dir():
        # Log output directory exists
        logging.info(f'Output Directory Exists at: {output_directory}')

    else:
        output_directory.mkdir(parents=True, exist_ok=True)
        # Log create output directory
        logging.info(f'Output Directory created at: {output_directory}')

    # Log the amount of archived to unpack
    logging.info(f'Unpacking: {len(source_files)} archives')

    if overwrite:
        # Log whether we will overwrite archives or not
        logger.info(f'Overwriting existing unpacked archives: {overwrite}')

    if delete_source:
        # log whether we will delete source directories after archiging
        logging.info(f'Deleting source archives after unpacking: {delete_source}')

    for source_file in source_files:

        source_file = Path(source_file)

        # if we are not overwriting, check if unpacked archive directory exists, if it does, skip
        if not overwrite:

            unpacked_archive_filepath = Path(output_directory, Path(source_file).stem)

            # if the archive already exists, skip it
            if unpacked_archive_filepath.is_dir():

                # log that we skip
                logging.info(f'{source_file}: unpacked archive already exists at {unpacked_archive_filepath}, Skipping...')
                # remove from list of source files
                source_files.remove(source_file)

            else:
                unpack_archive(
                    source_file,
                    output_directory,
                    logger,
                    delete_source
                )

        # else if we are overwriting, then archive every file
        else:
            unpack_archive(
                source_file,
                output_directory,
                logger,
                delete_source
            )

    end_time = time.time()
    total_time = end_time - start_time

    # Log script completion, including total number of archives created
    logging.info(f'Unpacking Archives Finished! Total Directories Created: {len(source_file)}')
    logging.info(f'Total Time Elapsed: {get_time_hh_mm_ss(total_time)}')


if __name__ == "__main__":

    # get cmd line arguments
    args = parse_arguments()

    # get the cmd line args
    source_files = args.source_files
    output_directory = args.output_directory
    overwrite = args.overwrite
    delete_source = args.delete_source
    log_level = args.log_level

    # run main function
    main(
        source_files=source_files,
        output_directory=output_directory,
        overwrite=overwrite,
        delete_source=delete_source,
        log_level=log_level,
    )
