"""Trusted operator command: DATABASE_URL=... python -m scripts.import_data FILE.csv [--init]."""
import argparse
from pathlib import Path
from services.data import parse_csv
from services.database import metadata,engine,ingest_calls

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('csv_file',type=Path)
    parser.add_argument('--init',action='store_true',help='Create prototype table; use controlled migrations in production')
    args=parser.parse_args()
    calls=parse_csv(args.csv_file.read_bytes())
    db=engine()
    if args.init:
        metadata.create_all(db)
    print(f'Imported {ingest_calls(calls,db)} aggregate calls')

if __name__=='__main__':
    main()
