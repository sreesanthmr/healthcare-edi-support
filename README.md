# Healthcare EDI Integration & Support System

A Python-based healthcare EDI integration and support system that simulates the processing of healthcare enrollment files received from insurance carriers through SFTP.

The project demonstrates EDI/X12 834 parsing, carrier-specific configuration, data validation, PostgreSQL storage, SFTP file transfer, duplicate-file detection, transaction handling, logging, error handling, file archival, processing history, and failed-file reprocessing.

> **Disclaimer:** This project uses synthetic healthcare data for demonstration and learning purposes. It is not a production HIPAA-compliant system and must not be used with real patient data.

---

## Project Overview

Healthcare organizations and benefits systems exchange structured enrollment information between carriers, vendors, and internal systems. EDI 834 is commonly used to communicate health plan enrollment and maintenance information.

This project simulates a simplified integration workflow in which files are placed on an SFTP server, downloaded by a Python service, validated and parsed, stored in PostgreSQL, and then moved to an archive or error location depending on the processing result.

### High-Level Workflow

```text
Insurance Carrier
       |
       | EDI 834 File
       v
   SFTP Server
       |
       | Download
       v
Python Integration Service
       |
       +--> SHA-256 File Hash
       |
       +--> Duplicate Check
       |
       +--> EDI Envelope Validation
       |
       +--> EDI Parsing
       |
       +--> Member Validation
       |
       +--> Data Transformation
       |
       +--> PostgreSQL Transaction
       |
       +--> Processing Log
       |
       +--> Archive / Error Handling
       |
       +--> Failed File Reprocessing
       v
PostgreSQL Database
```

---

## Objectives

The project was built to demonstrate practical skills relevant to system integration and application support, including:

- Processing structured EDI files using Python.
- Working with EDI/X12 834 healthcare enrollment data.
- Configuring different carrier mappings without hard-coding every mapping in the parser.
- Establishing and using SFTP connections for file transfer.
- Validating EDI envelopes and member-level data before database insertion.
- Preventing duplicate processing using SHA-256 file hashes.
- Using PostgreSQL transactions so that a failed file does not result in partial database updates.
- Maintaining processing history, status, attempt information, and error details.
- Separating successful, failed, and archived files.
- Reprocessing previously failed files after an issue has been corrected.
- Writing automated tests for important parts of the integration workflow.

---

## Key Features

### EDI 834 Processing

The application reads EDI/X12 834 files, separates them into segments, validates the envelope, and extracts selected enrollment/member information using a carrier-specific configuration.

### Carrier-Specific Configuration

Carrier mappings are stored in JSON configuration files instead of being hard-coded directly into the processing logic. This allows the same processing framework to work with different carrier layouts or element mappings.

The carrier registry contains information such as:

- Carrier name.
- EDI configuration file.
- Remote SFTP incoming directory.
- Remote archive directory.
- Remote error directory.

Example configuration structure:

```text
config/
├── carriers.json
├── carrier_abc.json
└── carrier_xyz.json
```

The `ABC` and `XYZ` configurations in this project are synthetic examples created to demonstrate configuration-driven processing. They do not represent real insurance-carrier specifications.

### SFTP File Transfer

The project uses Paramiko for SFTP communication. An SFTP server is provided locally using Docker so the complete file-transfer workflow can be tested without relying on an external server.

The application can:

- Connect to the SFTP server.
- List files in carrier-specific incoming directories.
- Download EDI files.
- Move successfully processed files to the remote archive directory.
- Move failed files to the remote errors directory.
- Move successfully reprocessed files from the remote errors directory to the archive directory.

### Duplicate File Detection

Before processing a downloaded file, the application calculates its SHA-256 hash and checks the processing history for the same carrier and file hash.

A previously successful or successfully reprocessed file is treated as a duplicate and is not processed again.

```text
Incoming File
     |
     v
Calculate SHA-256
     |
     v
Check Processing History
     |
     +---- Duplicate ----> Log + Archive
     |
     +---- New ----------> Continue Processing
```

### EDI Envelope Validation

The project validates important EDI envelope and transaction structure before attempting database processing.

The validation checks include:

- Required envelope segments such as `ISA`, `GS`, `ST`, `SE`, `GE`, and `IEA`.
- Confirmation that the transaction is an 834 transaction.
- Matching transaction control information between `ST` and `SE`.
- Matching group control information between `GS` and `GE`.
- Matching interchange control information between `ISA` and `IEA`.

This prevents malformed or structurally inconsistent EDI files from being inserted into the database.

### Member Data Validation

After parsing, each member record is validated before it is stored.

The validation includes required member information and basic format checks such as:

- Required member ID.
- Required first and last name.
- Date of birth format.
- Gender value/format.
- Health plan information.
- Effective date format.

The validation logic is intentionally simplified for demonstration purposes and is not intended to be a complete implementation of an industry EDI validation specification.

### Transactional Database Processing

Member records are written to PostgreSQL inside a database transaction.

The processing logic follows an all-or-nothing approach for a file:

```text
Start Transaction
      |
      v
Validate all member records
      |
      v
Save records
      |
      +---- Success ----> Commit
      |
      +---- Failure ----> Rollback
```

This helps prevent a file from leaving partially processed member data in the database.

### Database Upsert Handling

Member records use conflict handling so that an existing member can be updated instead of producing an uncontrolled duplicate database row.

The implementation uses PostgreSQL conflict handling based on the member identifier.

### Processing History and Attempt Tracking

Each file-processing attempt is recorded in `file_processing_log`.

The processing history captures information such as:

- File name.
- Processing status.
- Record count.
- Error message when applicable.
- Processing type.
- Carrier name.
- File hash.
- Attempt information.

Typical statuses include:

```text
SUCCESS
FAILED
DUPLICATE
REPROCESSED
REPROCESS_FAILED
```

This provides an operational history that can be used when investigating file-processing issues.

### Error Handling and Archival

The application separates files according to their processing result.

For a new incoming file:

```text
Remote SFTP
   |
   +--> Successful --> archive
   |
   +--> Failed -----> errors
```

The corresponding local copy follows the same lifecycle:

```text
Local Data
   |
   +--> incoming --> archive
   |
   +--> incoming --> errors
```

This mirrored structure keeps local and remote file locations easy to understand during troubleshooting.

### Failed File Reprocessing

A failed file is kept in the carrier-specific `errors` directory so that it can be investigated and processed again after the underlying issue has been addressed.

For successful reprocessing:

```text
errors
  |
  | Reprocess
  v
Processing
  |
  v
PostgreSQL
  |
  v
archive
```

Both the local and remote copies are moved from `errors` to `archive` after successful reprocessing.

If reprocessing fails again, the file remains in the error location and another attempt can be made after further investigation.

In a real operational environment, the source data should generally be corrected by the responsible carrier/vendor when the error is caused by incorrect source information. Internal processing defects or mapping issues can be corrected in the integration service and the original file can then be reprocessed.

---

## Project Structure

```text
healthcare-edi-support/
│
├── app/
│   ├── __init__.py
│   ├── config_loader.py
│   ├── database.py
│   ├── file_utils.py
│   ├── logger.py
│   ├── parser.py
│   ├── processor.py
│   ├── reprocessor.py
│   ├── sftp_client.py
│   └── validator.py
│
├── config/
│   ├── carriers.json
│   ├── carrier_abc.json
│   └── carrier_xyz.json
│
├── data/
│   ├── abc/
│   │   ├── incoming/
│   │   ├── archive/
│   │   └── errors/
│   └── xyz/
│       ├── incoming/
│       ├── archive/
│       └── errors/
│
├── samples/
│   ├── valid_834.txt
│   └── ...
│
├── sql/
│   ├── schema.sql
│   └── support_queries.sql
│
├── tests/
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_processor.py
│   ├── test_file_utils.py
│   ├── test_sftp.py
│   └── test_reprocessor.py
│
├── .env
├── .gitignore
├── docker-compose.yml
├── main.py
├── reprocess.py
├── requirements.txt
└── README.md
```

> `data/`, `.env`, logs, virtual environments, caches, and other local runtime files should not be committed to Git. Synthetic sample EDI files under `samples/` can be committed for demonstration and testing.

---

## Local and Remote File Layout

The local and remote SFTP directory structures intentionally mirror each other.

### Local

```text
data/
├── abc/
│   ├── incoming/
│   ├── archive/
│   └── errors/
└── xyz/
    ├── incoming/
    ├── archive/
    └── errors/
```

### SFTP Server

```text
sftp-server/data/
├── abc/
│   ├── incoming/
│   ├── archive/
│   └── errors/
└── xyz/
    ├── incoming/
    ├── archive/
    └── errors/
```

The carrier-specific structure prevents files belonging to one carrier from being mixed with another carrier's files.

---

## EDI 834 Data Processing

The parser works with the segment-based structure of an EDI/X12 document.

A simplified example is:

```text
ISA*...~
GS*BE*...~
ST*834*0001~
NM1*IL*1*DOE*JOHN****MI*ABC123~
DMG*D8*19800101*M~
HD*030**HLT~
DTP*348*D8*20260101~
SE*...~
GE*...~
IEA*...~
```

The parser extracts selected values from relevant segments according to the active carrier configuration.

For example, the configuration can specify which element contains:

```text
member_id
first_name
last_name
DOB
Gender
health_plan
effective_date
```

The implementation is intentionally limited to the sample 834 structure required by this project rather than attempting to implement every possible X12 834 variation.

---

## Carrier Configuration

The processing application loads a carrier registry from:

```text
config/carriers.json
```

The registry points to individual carrier mapping files.

A simplified configuration concept is:

```text
carriers.json
    |
    +--> abc
    |      |
    |      +--> carrier_abc.json
    |
    +--> xyz
           |
           +--> carrier_xyz.json
```

This design separates:

1. **Carrier-level operational settings** such as SFTP directories.
2. **EDI mapping settings** such as segment and element positions.
3. **Processing logic** implemented in Python.

As a result, carrier-specific changes can often be handled through configuration rather than modifying the core parser.

---

## Application Processing Flow

The main application processes each configured carrier independently.

For every carrier, it:

1. Loads the carrier configuration.
2. Creates the required local directories.
3. Connects to the carrier's SFTP incoming directory.
4. Lists EDI files.
5. Downloads each file to the local `incoming` directory.
6. Calculates the SHA-256 file hash.
7. Checks whether the file has already been successfully processed.
8. Validates the EDI envelope.
9. Parses the EDI 834 data.
10. Validates the member records.
11. Saves the records inside a PostgreSQL transaction.
12. Records the processing result in the processing log.
13. Moves the file to `archive` on success or `errors` on failure.

### Successful Processing

```text
SFTP incoming
      |
      v
Download
      |
      v
Duplicate Check
      |
      v
EDI Validation
      |
      v
Parse
      |
      v
Member Validation
      |
      v
PostgreSQL Transaction
      |
      v
Processing Log
      |
      v
Archive
```

### Failed Processing

```text
SFTP incoming
      |
      v
Download
      |
      v
Validation / Processing Failure
      |
      +--> Processing Log
      |
      +--> Local errors/
      |
      +--> Remote errors/
```

---

## Database

The project uses PostgreSQL for persistent storage.

The main tables used by the application are:

### `members`

Stores the parsed enrollment/member information extracted from EDI 834 files.

### `file_processing_log`

Stores file-level processing history and operational information such as status, carrier, record count, processing type, file hash, attempt information, and error details.

This separation allows the application to distinguish between business data and operational processing history.

---

## Support and Troubleshooting Queries

The project includes SQL examples under:

```text
sql/support_queries.sql
```

These queries can be used to inspect processing history and investigate issues such as:

- Recently failed files.
- Successful processing attempts.
- Reprocessing attempts.
- Processing history for a particular file.
- Files associated with a particular carrier.
- Duplicate-processing records.

The SQL is intended as a simple support-oriented reference rather than a complete production monitoring solution.

---

## Logging

Application logs are written to:

```text
logs/edi_processor.log
```

The logger records operational events such as:

- SFTP connection events.
- Carrier configuration loading.
- File discovery.
- File download.
- File processing start/end.
- Validation failures.
- Database-processing results.
- File movement to archive/error directories.
- Reprocessing attempts.

Sensitive information such as passwords and credentials should not be written to logs.

---

## Security Considerations

The project was designed with basic secure data-handling concepts in mind, while remaining a local learning project.

### Credentials

SFTP and database credentials are read from environment variables rather than being hard-coded into the application.

Example variables include:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
SFTP_HOST
SFTP_PORT
SFTP_USERNAME
SFTP_PASSWORD
```

The actual `.env` file should not be committed to Git.

### SFTP

Files are transferred through SFTP rather than unencrypted FTP.

The local Docker SFTP server is intended only for development and demonstration. A production environment would normally use stronger credential management and SSH key-based authentication where appropriate.

### Healthcare Data

This project uses synthetic data only. No real patient information should be placed in the repository or test environment.

The project demonstrates concepts relevant to handling sensitive healthcare information, but it does **not** provide HIPAA compliance by itself. A production healthcare system would require appropriate administrative, technical, physical, operational, access-control, auditing, encryption, infrastructure, and compliance controls.

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd healthcare-edi-support
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Example structure:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=healthcare_edi
DB_USER=postgres
DB_PASSWORD=your_password

SFTP_HOST=localhost
SFTP_PORT=2222
SFTP_USERNAME=ediuser
SFTP_PASSWORD=your_password
```

Use values appropriate for your local environment. Do not commit real credentials.

### 5. Create the PostgreSQL Database

Create a PostgreSQL database matching the value configured in `.env`.

Then execute the schema file:

```bash
psql -U postgres -d healthcare_edi -f sql/schema.sql
```

The exact PostgreSQL command may vary depending on how PostgreSQL is installed and configured on your machine.

### 6. Start the Local SFTP Server

The project includes Docker configuration for a local SFTP environment.

Start it with:

```bash
docker compose up -d
```

Check the running containers with:

```bash
docker ps
```

The SFTP service is exposed locally through port `2222` in the development setup.

### 7. Prepare Sample Files

Place synthetic EDI files in the appropriate SFTP carrier incoming directory, for example:

```text
sftp-server/data/abc/incoming/
sftp-server/data/xyz/incoming/
```

Only synthetic/sample files should be used.

---

## Running the Application

After PostgreSQL and the Docker SFTP server are available:

```bash
python main.py
```

The application loads all configured carriers and processes EDI files from their configured SFTP incoming directories.

A successful file follows this path:

```text
SFTP incoming
     ↓
Local incoming
     ↓
Process
     ↓
PostgreSQL
     ↓
Local archive
     ↓
SFTP archive
```

A failed file follows this path:

```text
SFTP incoming
     ↓
Local incoming
     ↓
Processing failure
     ↓
Local errors
     ↓
SFTP errors
```

---

## Reprocessing a Failed File

Use the root-level `reprocess.py` command to retry a failed file.

```bash
python reprocess.py <carrier> <file_name>
```

Example:

```bash
python reprocess.py abc failed_834.txt
```

The application looks for the failed file under:

```text
data/<carrier>/errors/
```

It then processes the file using the correct carrier configuration.

### Successful Reprocessing

```text
data/abc/errors/failed_834.txt
             |
             v
         Reprocess
             |
             v
        PostgreSQL
             |
             v
data/abc/archive/failed_834.txt
```

The corresponding remote SFTP file is also moved from the carrier's `errors` directory to the remote `archive` directory.

### Failed Reprocessing

If the file fails again:

```text
data/abc/errors/failed_834.txt
```

remains available for investigation and another attempt.

---

## Testing

The project includes automated tests using `pytest`.

Run the complete test suite with:

```bash
pytest -v
```

The tests cover the main integration components, including:

- EDI parsing.
- EDI envelope and member validation.
- File processing behavior.
- SHA-256 file hashing.
- SFTP-related behavior using test doubles/mocks where appropriate.
- Failed-file reprocessing.

The project test suite currently passes successfully in the development environment.

---

## Example Processing Scenarios

### Scenario 1: Valid EDI File

```text
File received
    ↓
Hash calculated
    ↓
Not a duplicate
    ↓
Envelope valid
    ↓
Members parsed and validated
    ↓
Database transaction committed
    ↓
Status = SUCCESS
    ↓
File archived
```

### Scenario 2: Invalid EDI Structure

```text
File received
    ↓
Envelope validation fails
    ↓
Status = FAILED
    ↓
Error recorded
    ↓
File moved to errors
```

### Scenario 3: Duplicate File

```text
File received
    ↓
SHA-256 calculated
    ↓
Matching successful file found
    ↓
Status = DUPLICATE
    ↓
File is not processed again
```

### Scenario 4: Temporary/Internal Processing Issue

```text
File received
    ↓
Processing fails
    ↓
File moved to errors
    ↓
Issue investigated/fixed
    ↓
Original file reprocessed
    ↓
Success
    ↓
File moved to archive
```

### Scenario 5: Incorrect Source Data

When an error is caused by incorrect source information, the expected operational approach is to identify the validation problem and coordinate with the responsible carrier/vendor for a corrected file rather than manually changing the source EDI document.

Once a corrected file is received, it can go through the normal processing workflow.

---

## Troubleshooting Guide

### SFTP Connection Fails

Check:

```text
SFTP_HOST
SFTP_PORT
SFTP_USERNAME
SFTP_PASSWORD
```

Also confirm that the Docker SFTP container is running:

```bash
docker ps
```

### PostgreSQL Connection Fails

Check that PostgreSQL is running and that the values in `.env` match the actual database configuration.

### File Is Not Being Processed

Check:

1. The file is located in the correct carrier's SFTP `incoming` directory.
2. The file has a `.txt` extension.
3. The carrier exists in `config/carriers.json`.
4. The carrier configuration file exists.
5. The application log contains the file-processing event.

### File Was Moved to `errors`

Inspect the error message in:

```text
logs/edi_processor.log
```

and review the corresponding entry in `file_processing_log`.

### Reprocessing Cannot Find the File

Confirm that the file exists at:

```text
data/<carrier>/errors/<file_name>
```

and that the carrier key passed to `reprocess.py` matches the carrier configured in `config/carriers.json`.

---

## Design Decisions

### Why Configuration-Driven Parsing?

Different carriers can use different mappings or layouts. Keeping mappings in JSON makes the parser reusable and reduces the need to modify Python code for every carrier-specific change.

### Why SHA-256?

The file hash provides a deterministic fingerprint for the file contents. It can be stored with processing history and used to detect a file that has already been successfully processed.

### Why PostgreSQL Transactions?

A healthcare enrollment file may contain multiple member records. Using a transaction allows the application to avoid committing a partial set of records when processing the file fails.

### Why Separate `incoming`, `archive`, and `errors`?

The directory lifecycle makes the operational state of a file easy to understand and supports troubleshooting and reprocessing without mixing active, completed, and failed files.

### Why Keep Failed Files Instead of Editing Them?

Keeping the original failed file provides a reliable record of what was received. If the source data is incorrect, the responsible carrier/vendor can provide a corrected file. If the processing logic is incorrect, the original file can be reprocessed after the application issue is fixed.

---

## Limitations

This project is a learning and portfolio simulation and has several limitations compared with a production healthcare integration platform:

- It supports only the simplified EDI 834 structures required by the project.
- It does not implement every X12 rule, loop, segment, or qualifier.
- The local Docker SFTP environment is not a production SFTP deployment.
- Authentication and secret management are simplified for local development.
- The validation rules are intentionally limited.
- It does not implement a production monitoring, alerting, or job-scheduling platform.
- It does not claim HIPAA compliance.
- The project does not process real patient or production healthcare data.

---

## Possible Future Improvements

Potential extensions include:

- Support for additional X12 transaction types such as 270/271 or 834 variations.
- More complete EDI envelope and business-rule validation.
- SSH key-based SFTP authentication and stronger secret management.
- Automated monitoring and alerting for failed files.
- Retry policies for temporary transfer or infrastructure failures.
- More detailed operational reporting.
- Additional carrier configurations.
- Improved automated integration tests using a dedicated test SFTP and PostgreSQL environment.
- Structured application metrics and centralized log management.

---

## Skills Demonstrated

This project demonstrates practical exposure to:

```text
Python
SQL
PostgreSQL
EDI/X12 834
SFTP / Paramiko
Docker
JSON / XML-style structured data concepts
Data Validation
Database Transactions
SHA-256 Hashing
Error Handling
Logging
File Processing
Configuration Management
pytest
Troubleshooting and Reprocessing
```

It is particularly focused on the kind of work involved in system integration and support: receiving files, validating data, processing records, recording failures, troubleshooting issues, maintaining operational history, and safely reprocessing failed files.

---

## Disclaimer

This repository is intended only as a portfolio and educational project.

All healthcare-related files and member information used by the project are synthetic. No real patient information or production healthcare data should be added to the repository.

The project demonstrates technical concepts related to EDI processing, SFTP file transfer, validation, database operations, troubleshooting, and healthcare data handling. It does not constitute a HIPAA-compliant production system.
