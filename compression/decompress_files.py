import pathlib
import shutil
import logging
import argparse
import time
from datetime import timedelta, datetime
from pathlib import Path
from typing import Union, List
from enum import Enum
from utils import get_folder_size, get_file_size, get_time_hh_mm_ss, setup_logger


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

    args = p.parse_args()

    return args


def unpack_archive(
        source_file: Union[str, pathlib.Path],
        output_directory: Union[str, pathlib.Path],
        logger: logging.Logger,
        delete: bool,
) -> None:

    try:
        # Log the start of the unpacking process
        logging.info(f'Starting unpacking archive from file: {source_file}')

        # get the size of the archive file
        archive_size = get_file_size(source_file)

        # if there was no error during calculating source archive size, print it out
        if archive_size:
            # print the size of the original directory
            logging.info(f'Original Archive Size: {archive_size:.2f}')

        # Unpack the archive
        shutil.unpack_archive(source_file, output_directory)

        output_archive_path = Path(output_directory, Path(source_file.stem))

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

            # delete source dir
            shutil.rmtree(source_file)

    except Exception as e:
        # log any errors during unpacking
        logger.error(f"An error occurred during unpacking: {str(e)}")

    return None


def main(
        source_files: List[str],
        output_directory: Union[str, Path],
        overwrite: bool,
        delete_source: bool,
) -> None:

    start_time = time.time()

    logger = setup_logger(output_directory, log_type='decompression')

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
        logger.warning(f'Overwriting existing unpacked archives: {overwrite}')

    if delete_source:
        # log whether we will delete source directories after archiging
        logging.warning(f'Deleting source archives after unpacking: {delete_source}')

    for source_file in source_files:

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
    logging.info(f'Unpacking Archives Finished! Total Directories Created: {len(source_filee)}')
    logging.info(f'Total Time Elapsed: {get_time_hh_mm_ss(total_time)}')


if __name__ == "__main__":

    # get cmd line arguments
    args = parse_arguments()

    # get the cmd line args
    source_files = args.source_files
    output_directory = args.output_directory
    overwrite = args.overwrite
    delete_source = args.delete_source

    # run main function
    main(
        source_files=source_files,
        output_directory=output_directory,
        overwrite=overwrite,
        delete_source=delete_source,
    )
