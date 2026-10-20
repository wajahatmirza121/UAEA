"""Expanded catalogue, student records and WhatsApp OTP challenges.

Revision ID: 0002_expanded_db_otp
Revises: 0001_initial
Create Date: 2026-10-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_expanded_db_otp"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('academic_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('term', sa.String(length=40), nullable=False),
    sa.Column('program_code', sa.String(length=20), nullable=True),
    sa.Column('level', sa.String(length=40), nullable=True),
    sa.Column('event', sa.String(length=120), nullable=False),
    sa.Column('event_ur', sa.String(length=120), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('source_doc_ref', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_events_program_code'), 'academic_events', ['program_code'], unique=False)
    op.create_index(op.f('ix_academic_events_term'), 'academic_events', ['term'], unique=False)
    op.create_table('otp_challenges',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=100), nullable=False),
    sa.Column('roll_number', sa.String(length=30), nullable=False),
    sa.Column('phone', sa.String(length=30), nullable=False),
    sa.Column('code_hash', sa.String(length=128), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('pending_tool', sa.JSON(), nullable=True),
    sa.Column('pending_question', sa.Text(), nullable=True),
    sa.Column('delivery', sa.String(length=40), nullable=True),
    sa.Column('delivery_ref', sa.String(length=120), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('verified_until', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_otp_challenges_roll_number'), 'otp_challenges', ['roll_number'], unique=False)
    op.create_index(op.f('ix_otp_challenges_session_id'), 'otp_challenges', ['session_id'], unique=False)
    op.create_table('scholarships',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('name_ur', sa.String(length=200), nullable=True),
    sa.Column('kind', sa.String(length=60), nullable=False),
    sa.Column('coverage', sa.String(length=200), nullable=False),
    sa.Column('eligibility', sa.Text(), nullable=False),
    sa.Column('deadline', sa.Date(), nullable=True),
    sa.Column('seats', sa.Integer(), nullable=True),
    sa.Column('how_to_apply', sa.Text(), nullable=True),
    sa.Column('source_doc_ref', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('class_schedules',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('term', sa.String(length=40), nullable=False),
    sa.Column('program_code', sa.String(length=20), nullable=False),
    sa.Column('semester_no', sa.Integer(), nullable=False),
    sa.Column('section', sa.String(length=10), nullable=False),
    sa.Column('campus_id', sa.String(length=36), nullable=True),
    sa.Column('day', sa.String(length=12), nullable=False),
    sa.Column('start_time', sa.String(length=5), nullable=False),
    sa.Column('end_time', sa.String(length=5), nullable=False),
    sa.Column('course_code', sa.String(length=20), nullable=False),
    sa.Column('course_title', sa.String(length=200), nullable=False),
    sa.Column('room', sa.String(length=40), nullable=True),
    sa.Column('instructor_name', sa.String(length=160), nullable=True),
    sa.ForeignKeyConstraint(['campus_id'], ['campuses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_schedules_program_code'), 'class_schedules', ['program_code'], unique=False)
    op.create_table('hostels',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('campus_id', sa.String(length=36), nullable=True),
    sa.Column('gender', sa.String(length=10), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=False),
    sa.Column('vacant_seats', sa.Integer(), nullable=True),
    sa.Column('room_type', sa.String(length=120), nullable=True),
    sa.Column('fee_per_semester', sa.Integer(), nullable=False),
    sa.Column('mess_fee_per_month', sa.Integer(), nullable=True),
    sa.Column('facilities', sa.JSON(), nullable=True),
    sa.Column('warden_name', sa.String(length=160), nullable=True),
    sa.Column('warden_phone', sa.String(length=40), nullable=True),
    sa.Column('source_doc_ref', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['campus_id'], ['campuses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transport_routes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('route_no', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('campus_id', sa.String(length=36), nullable=True),
    sa.Column('stops', sa.JSON(), nullable=True),
    sa.Column('morning_departure', sa.String(length=10), nullable=True),
    sa.Column('evening_departure', sa.String(length=10), nullable=True),
    sa.Column('fee_per_semester', sa.Integer(), nullable=True),
    sa.Column('driver_contact', sa.String(length=40), nullable=True),
    sa.ForeignKeyConstraint(['campus_id'], ['campuses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('faculty',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('designation', sa.String(length=80), nullable=False),
    sa.Column('department_id', sa.String(length=36), nullable=True),
    sa.Column('program_codes', sa.JSON(), nullable=True),
    sa.Column('email', sa.String(length=160), nullable=True),
    sa.Column('office', sa.String(length=120), nullable=True),
    sa.Column('office_hours', sa.String(length=120), nullable=True),
    sa.Column('specialization', sa.String(length=255), nullable=True),
    sa.Column('qualification', sa.String(length=160), nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('programs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('name_ur', sa.String(length=255), nullable=True),
    sa.Column('level', sa.String(length=40), nullable=False),
    sa.Column('faculty', sa.String(length=120), nullable=False),
    sa.Column('department_id', sa.String(length=36), nullable=True),
    sa.Column('duration_years', sa.Float(), nullable=False),
    sa.Column('semesters', sa.Integer(), nullable=False),
    sa.Column('credit_hours', sa.Integer(), nullable=False),
    sa.Column('seats', sa.Integer(), nullable=True),
    sa.Column('shift', sa.String(length=60), nullable=True),
    sa.Column('eligibility', sa.Text(), nullable=True),
    sa.Column('min_percentage', sa.Integer(), nullable=True),
    sa.Column('entry_test', sa.String(length=255), nullable=True),
    sa.Column('campuses', sa.JSON(), nullable=True),
    sa.Column('aliases', sa.JSON(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('source_doc_ref', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_programs_code'), 'programs', ['code'], unique=True)
    op.create_table('courses',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('credit_hours', sa.Integer(), nullable=False),
    sa.Column('program_code', sa.String(length=20), nullable=False),
    sa.Column('semester_no', sa.Integer(), nullable=False),
    sa.Column('instructor_id', sa.String(length=36), nullable=True),
    sa.Column('prerequisite', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['instructor_id'], ['faculty.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_code'), 'courses', ['code'], unique=False)
    op.create_index(op.f('ix_courses_program_code'), 'courses', ['program_code'], unique=False)
    op.create_table('students',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('roll_number', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('father_name', sa.String(length=160), nullable=True),
    sa.Column('gender', sa.String(length=10), nullable=True),
    sa.Column('program_code', sa.String(length=20), nullable=False),
    sa.Column('campus_id', sa.String(length=36), nullable=True),
    sa.Column('batch', sa.String(length=20), nullable=True),
    sa.Column('section', sa.String(length=10), nullable=True),
    sa.Column('current_semester', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('cgpa', sa.Float(), nullable=True),
    sa.Column('phone', sa.String(length=30), nullable=False),
    sa.Column('email', sa.String(length=160), nullable=True),
    sa.Column('cnic_masked', sa.String(length=20), nullable=True),
    sa.Column('hostel_id', sa.String(length=36), nullable=True),
    sa.Column('advisor_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['advisor_id'], ['faculty.id'], ),
    sa.ForeignKeyConstraint(['campus_id'], ['campuses.id'], ),
    sa.ForeignKeyConstraint(['hostel_id'], ['hostels.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_students_program_code'), 'students', ['program_code'], unique=False)
    op.create_index(op.f('ix_students_roll_number'), 'students', ['roll_number'], unique=True)
    op.create_table('attendance_records',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('roll_number', sa.String(length=30), nullable=False),
    sa.Column('term', sa.String(length=40), nullable=False),
    sa.Column('course_code', sa.String(length=20), nullable=False),
    sa.Column('course_title', sa.String(length=200), nullable=False),
    sa.Column('attended', sa.Integer(), nullable=False),
    sa.Column('total', sa.Integer(), nullable=False),
    sa.Column('percentage', sa.Float(), nullable=False),
    sa.Column('updated_on', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['roll_number'], ['students.roll_number'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attendance_records_roll_number'), 'attendance_records', ['roll_number'], unique=False)
    op.create_table('fee_records',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('roll_number', sa.String(length=30), nullable=False),
    sa.Column('term', sa.String(length=40), nullable=False),
    sa.Column('challan_no', sa.String(length=40), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('late_fine', sa.Integer(), nullable=False),
    sa.Column('scholarship_discount', sa.Integer(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('paid_on', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('bank', sa.String(length=80), nullable=True),
    sa.ForeignKeyConstraint(['roll_number'], ['students.roll_number'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fee_records_roll_number'), 'fee_records', ['roll_number'], unique=False)
    op.create_table('result_records',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('roll_number', sa.String(length=30), nullable=False),
    sa.Column('term', sa.String(length=40), nullable=False),
    sa.Column('semester_no', sa.Integer(), nullable=False),
    sa.Column('gpa', sa.Float(), nullable=False),
    sa.Column('cgpa', sa.Float(), nullable=False),
    sa.Column('credit_hours', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('courses', sa.JSON(), nullable=False),
    sa.Column('published_on', sa.Date(), nullable=True),
    sa.Column('gazette_ref', sa.String(length=80), nullable=True),
    sa.ForeignKeyConstraint(['roll_number'], ['students.roll_number'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_result_records_roll_number'), 'result_records', ['roll_number'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_result_records_roll_number'), table_name='result_records')
    op.drop_table('result_records')
    op.drop_index(op.f('ix_fee_records_roll_number'), table_name='fee_records')
    op.drop_table('fee_records')
    op.drop_index(op.f('ix_attendance_records_roll_number'), table_name='attendance_records')
    op.drop_table('attendance_records')
    op.drop_index(op.f('ix_students_roll_number'), table_name='students')
    op.drop_index(op.f('ix_students_program_code'), table_name='students')
    op.drop_table('students')
    op.drop_index(op.f('ix_courses_program_code'), table_name='courses')
    op.drop_index(op.f('ix_courses_code'), table_name='courses')
    op.drop_table('courses')
    op.drop_index(op.f('ix_programs_code'), table_name='programs')
    op.drop_table('programs')
    op.drop_table('faculty')
    op.drop_table('transport_routes')
    op.drop_table('hostels')
    op.drop_index(op.f('ix_class_schedules_program_code'), table_name='class_schedules')
    op.drop_table('class_schedules')
    op.drop_table('scholarships')
    op.drop_index(op.f('ix_otp_challenges_session_id'), table_name='otp_challenges')
    op.drop_index(op.f('ix_otp_challenges_roll_number'), table_name='otp_challenges')
    op.drop_table('otp_challenges')
    op.drop_index(op.f('ix_academic_events_term'), table_name='academic_events')
    op.drop_index(op.f('ix_academic_events_program_code'), table_name='academic_events')
    op.drop_table('academic_events')
