# Theseus

Theseus is a web-based document editor with integrated Git-like VCS and AI capabilities.

## Installation

1. Clone the repository
```
git clone https://github.com/b-chua-student/theseus
```
2. Install npm packages
```
npm install
```
3. Create Python virtual environment
```
cd backend
python -m venv .venv
source .venv/bin/activate
```

| Platform | Shell      | Command to activate virtual environment |
| -------- | ---------- | --------------------------------------- |
| POSIX    | bash/zsh   | `$ source <venv>/bin/activate`          |
| POSIX    | fish       | `$ source <venv>/bin/activate.fish`     |
| POSIX    | csh/tcsh   | `$ source <venv>/bin/activate.csh`      |
| POSIX    | pwsh       | `$ <venv>/bin/Activate.ps1`             |
| Windows  | cmd.exe    | `C:\> <venv>\Scripts\activate.bat`      |
| Windows  | PowerShell | `PS C:\> <venv>\Scripts\Activate.ps1`   |
4. Install pip packages (make sure you are inside the `backend/` folder)
```
pip install -r requirements.txt
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

## Running the Server

Ensure:
- You are in root folder
- Virtual environment is activate
```
npm run dev
```
This command runs both the frontend server (Vite) and backend server (Flask).

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
