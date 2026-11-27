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
source <command>
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

## Branching Strategy

This project uses [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow).

- `main` is always deployable and protected. No direct pushes.
- All work happens on short-lived branches created from `main`.
- Branch names are descriptive and prefixed by type, e.g. `feat/user-collections`, `fix/env-validation`.

<img width="2358" height="748" alt="image" src="https://github.com/user-attachments/assets/dacc018c-93e5-4e07-acb7-7aa1c9f80b0d" />

### Workflow

1. Create a branch from `main`.
2. Commit changes using the Commitizen format (`feat(scope): message`).
3. Push the branch and open a pull request.
4. CI runs on the PR: install, lint, build. All checks must pass.
5. Request review and address feedback.
6. Merge into `main` after approval.
7. Delete the branch.

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
