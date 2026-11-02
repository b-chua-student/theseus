from domain.shared.errors import DomainError

class ProjectError(DomainError):
    pass

class InvalidProjectNameError(ProjectError):
    pass

class InvalidDisplayNameError(ProjectError):
    pass

class InvalidEmailError(ProjectError):
    pass

class NotAProjectMemberError(ProjectError):
    pass

class IsCurrentOwnerError(ProjectError):
    pass
