import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_DATA_DIR = Path("data")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a Kaggle dataset from a URL and extract CSV files into the data directory."
    )
    parser.add_argument("url", help="Kaggle dataset URL, e.g. https://www.kaggle.com/datasets/owner/name")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory where CSV files should be extracted. Default: {DEFAULT_DATA_DIR}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing CSV files.",
    )
    return parser.parse_args()


def ensure_kaggle_cli() -> None:
    if shutil.which("kaggle") is None:
        raise RuntimeError(
            "Kaggle CLI not found. Install it with `pip install kaggle` and configure your Kaggle API credentials."
        )


def extract_dataset_slug(source_url: str) -> str:
    parsed = urlparse(source_url)
    parts = [part for part in parsed.path.split("/") if part]

    try:
        datasets_index = parts.index("datasets")
    except ValueError as exc:
        raise ValueError(f"Unsupported Kaggle dataset URL: {source_url}") from exc

    if len(parts) <= datasets_index + 2:
        raise ValueError(f"Incomplete Kaggle dataset URL: {source_url}")

    owner = parts[datasets_index + 1]
    dataset = parts[datasets_index + 2]
    return f"{owner}/{dataset}"


def extract_csvs(zip_path: Path, destination: Path, force: bool) -> list[Path]:
    extracted_files: list[Path] = []
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member.is_dir() or member_path.suffix.lower() != ".csv":
                continue

            output_path = destination / member_path.name
            if output_path.exists() and not force:
                print(f"Skipping existing file: {output_path}")
                extracted_files.append(output_path)
                continue

            with archive.open(member) as source_file, output_path.open("wb") as target_file:
                shutil.copyfileobj(source_file, target_file)

            extracted_files.append(output_path)
            print(f"Extracted: {output_path}")

    return extracted_files


def main() -> int:
    args = parse_args()

    try:
        ensure_kaggle_cli()
        slug = extract_dataset_slug(args.url)
        print(f"Downloading {slug}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            subprocess.run(
                [
                    "kaggle",
                    "datasets",
                    "download",
                    "-d",
                    slug,
                    "-p",
                    str(temp_path),
                    "--force",
                ],
                check=True,
            )

            zip_files = sorted(temp_path.glob("*.zip"))
            if not zip_files:
                raise FileNotFoundError(f"No zip archive downloaded for {slug}")

            extracted = extract_csvs(zip_files[0], args.data_dir, args.force)
            if not extracted:
                print("No CSV files found in the downloaded archive.")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
