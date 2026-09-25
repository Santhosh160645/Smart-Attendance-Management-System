from datetime import datetime

from sqlalchemy.orm import Session

from models.models import (
    Attendance,
    AttendanceCorrection,
    AuditLog,
    ClassSession,
    FacultySubject,
)


VALID_STATUSES = {
    "PRESENT",
    "ABSENT",
    "LATE",
}


def request_correction(
    db: Session,
    attendance_id: int,
    faculty_id: int,
    new_status: str,
    reason: str,
    user_id: int,
):
    """
    Create a correction request for an attendance record.
    Only the faculty assigned to the corresponding
    subject and section can request the correction.
    """

    new_status = new_status.upper().strip()
    reason = reason.strip()

    if new_status not in VALID_STATUSES:
        return False, "Invalid attendance status."

    if not reason:
        return False, "Correction reason is required."

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.id == attendance_id
        )
        .first()
    )

    if not attendance:
        return False, "Attendance record not found."

    session = (
        db.query(ClassSession)
        .filter(
            ClassSession.id == attendance.session_id
        )
        .first()
    )

    if not session:
        return False, "Attendance session not found."

    assignment = (
        db.query(FacultySubject)
        .filter(
            FacultySubject.faculty_id == faculty_id,
            FacultySubject.subject_id == session.subject_id,
            FacultySubject.section_id == session.section_id,
        )
        .first()
    )

    if not assignment:
        return (
            False,
            "You are not assigned to this subject and section.",
        )

    if new_status == attendance.status:
        return (
            False,
            "New attendance status must be different "
            "from the current status.",
        )

    pending_request = (
        db.query(AttendanceCorrection)
        .filter(
            AttendanceCorrection.attendance_id
            == attendance_id,
            AttendanceCorrection.status == "PENDING",
        )
        .first()
    )

    if pending_request:
        return (
            False,
            "A correction request is already pending "
            "for this attendance record.",
        )

    correction = AttendanceCorrection(
        attendance_id=attendance.id,
        requested_by=faculty_id,
        old_status=attendance.status,
        new_status=new_status,
        reason=reason,
        status="PENDING",
    )

    db.add(correction)

    audit_log = AuditLog(
        user_id=user_id,
        action="REQUEST_ATTENDANCE_CORRECTION",
        entity_type="ATTENDANCE_CORRECTION",
        details=(
            f"Correction requested for attendance "
            f"{attendance.id}: "
            f"{attendance.status} -> {new_status}. "
            f"Reason: {reason}"
        ),
    )

    db.add(audit_log)

    db.commit()
    db.refresh(correction)

    return (
        True,
        "Attendance correction request submitted successfully.",
    )


def review_correction(
    db: Session,
    correction_id: int,
    admin_user_id: int,
    decision: str,
):
    """
    Approve or reject an attendance correction.
    """

    decision = decision.upper().strip()

    if decision not in {"APPROVED", "REJECTED"}:
        return False, "Invalid correction decision."

    correction = (
        db.query(AttendanceCorrection)
        .filter(
            AttendanceCorrection.id
            == correction_id
        )
        .first()
    )

    if not correction:
        return False, "Correction request not found."

    if correction.status != "PENDING":
        return (
            False,
            "This correction request has already been reviewed.",
        )

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.id
            == correction.attendance_id
        )
        .first()
    )

    if not attendance:
        return False, "Attendance record not found."

    try:

        if decision == "APPROVED":

            attendance.status = correction.new_status
            attendance.updated_at = datetime.utcnow()

            correction.status = "APPROVED"

        else:

            correction.status = "REJECTED"

        correction.reviewed_by = admin_user_id
        correction.reviewed_at = datetime.utcnow()

        audit_log = AuditLog(
            user_id=admin_user_id,
            action=f"{decision}_ATTENDANCE_CORRECTION",
            entity_type="ATTENDANCE_CORRECTION",
            entity_id=correction.id,
            details=(
                f"Correction {decision.lower()}. "
                f"Attendance {correction.attendance_id}: "
                f"{correction.old_status} -> "
                f"{correction.new_status}."
            ),
        )

        db.add(audit_log)

        db.commit()

        return (
            True,
            f"Correction request {decision.lower()} successfully.",
        )

    except Exception as e:

        db.rollback()

        return (
            False,
            f"Unable to review correction: {e}",
        )