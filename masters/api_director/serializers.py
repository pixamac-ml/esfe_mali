# masters/api_director/serializers.py
from rest_framework import serializers
from programs.models import Program
from ..models import (
    MasterEnrollment, InstructorAssignment, ModuleUE, Exam, SemesterResult,
    Semester, Cohort
)

class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ["id", "title", "code", "cycle"]

class SemesterSerializer(serializers.ModelSerializer):
    program = ProgramSerializer(read_only=True)
    class Meta:
        model = Semester
        fields = ["id", "name", "order", "program", "ects_target"]

class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ["id", "label", "start_date", "end_date"]

class InstructorSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source="module.title", read_only=True)
    module_code = serializers.CharField(source="module.code", read_only=True)
    semester_name = serializers.CharField(source="module.semester.name", read_only=True)
    class Meta:
        model = InstructorAssignment
        fields = ["id", "instructor", "module_title", "module_code", "semester_name", "role"]

class ModuleSerializer(serializers.ModelSerializer):
    semester = SemesterSerializer(read_only=True)
    instructors = InstructorSerializer(many=True, read_only=True)
    class Meta:
        model = ModuleUE
        fields = ["id", "code", "title", "coefficient", "credits", "semester", "is_active", "instructors"]

class StudentSerializer(serializers.ModelSerializer):
    program = ProgramSerializer(read_only=True)
    cohort = CohortSerializer(read_only=True)
    class Meta:
        model = MasterEnrollment
        fields = ["id", "student", "program", "cohort", "status"]

class ExamSerializer(serializers.ModelSerializer):
    semester = SemesterSerializer(read_only=True)
    class Meta:
        model = Exam
        fields = ["id", "title", "eval_kind", "coefficient", "total_points", "start_at", "end_at", "semester"]

class SemesterResultSerializer(serializers.ModelSerializer):
    semester = SemesterSerializer(read_only=True)
    class Meta:
        model = SemesterResult
        fields = ["id", "average_20", "credits_earned", "decision", "is_locked", "computed_at", "semester"]
