# Smart Computer Lab Assist

A desktop app (Python + Tkinter) for managing computer lab assets and student complaints at Annasaheb Dange College of Engineering and Technology, Ashta.

## Features
- Students report PC issues without logging in
- Lab assistants log in to see a dashboard, manage assets, and resolve complaints
- Search computers by lab or PC number
- Export the asset list to CSV

## Requirements
- Python 3.10+
- MySQL or MariaDB running on localhost (for example through XAMPP)

## Setup
1. Install the packages:
```
   pip install -r requirements.txt
```
2. Create an empty database named `smart_lab_asset` (for example in phpMyAdmin).
3. Import the table structure from `schema.sql`:
```
   mysql -u root smart_lab_asset < schema.sql
```
4. Add sample PCs:
```
   python seed_data.py
```
5. Run the app:
```
   python app.py
```

## Note
`db.py` connects as `root` with an empty password on localhost. Change it to match your own setup.
