from ..models.case_assignment import CaseAssignment
from ..core.extensions import db


class CaseAssignmentRepository:

    @staticmethod
    def create(assignment: CaseAssignment):
        db.session.add(assignment)
        db.session.commit()
        return assignment

    @staticmethod
    def get_by_id(assignment_id: str):
        return CaseAssignment.query.get(assignment_id)

    @staticmethod
    def get_active_assignment_for_case(case_id: str):
        return CaseAssignment.query.filter_by(
            case_id=case_id, 
            status="active"
        ).first()

    @staticmethod
    def get_assignments_for_case(case_id: str):
        return CaseAssignment.query.filter_by(case_id=case_id).order_by(
            CaseAssignment.created_at.desc()
        ).all()

    @staticmethod
    def get_assignments_for_lawyer(lawyer_id: str):
        return CaseAssignment.query.filter_by(lawyer_id=lawyer_id).order_by(
            CaseAssignment.created_at.desc()
        ).all()

    @staticmethod
    def get_active_assignments_for_lawyer(lawyer_id: str):
        return CaseAssignment.query.filter_by(
            lawyer_id=lawyer_id, 
            status="active"
        ).all()

    @staticmethod
    def update(assignment: CaseAssignment):
        db.session.commit()
        return assignment

    @staticmethod
    def supersede_previous_assignments(case_id: str):
        previous_assignments = CaseAssignment.query.filter_by(
            case_id=case_id, 
            status="active"
        ).all()
        for assignment in previous_assignments:
            assignment.status = "superseded"
        db.session.commit()
        return previous_assignments
