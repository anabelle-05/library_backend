# api/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


def get_role(user):
    profile = getattr(user, "userprofile", None)
    return profile.role if profile else None


class IsLibrarian(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and get_role(request.user) == "librarian"

class LibrarianFullStudentReadOnly(BasePermission):
    """
    Students: GET and PATCH only
    Teachers: full CRUD
    Librarians: full CRUD
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = get_role(request.user)
        if role in ("librarian", "teacher"):
            return True
        if role == "student":
            # Allow safe methods + PATCH
            return request.method in (*SAFE_METHODS, "PATCH")
        return False


class BorrowedBookPermission(BasePermission):
    """
    Students/Teachers: can borrow (POST) and view own records only
    Librarians: full access to all records
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = get_role(request.user)
        if role == "librarian":
            return True
        return request.method in (*SAFE_METHODS, "POST")

    def has_object_permission(self, request, view, obj):
        if get_role(request.user) == "librarian":
            return True
        return obj.user == request.user


class UserProfilePermission(BasePermission):
    """
    Students/Teachers: view and edit own profile only
    Librarians: full access to all profiles
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if get_role(request.user) == "librarian":
            return True
        return obj.user == request.user


class BookSuggestionPermission(BasePermission):
    """
    Students/Teachers: create suggestions and view own only
    Librarians: full access (approve/reject)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = get_role(request.user)
        if role == "librarian":
            return True
        return request.method in (*SAFE_METHODS, "POST")

    def has_object_permission(self, request, view, obj):
        if get_role(request.user) == "librarian":
            return True
        return obj.requested_by == request.user
    
