from django.contrib import admin
from .models import (
    MasterProgram, Cohort, Semester, ModuleUE, Chapter, Lesson,
    LessonResource, LessonDiscussion, LessonQuiz, LessonQuizQuestion, LessonQuizAnswer,
    MasterEnrollment, InstructorAssignment,
    Assignment, Submission, Exam, ExamGrade,
    LessonProgress, ModuleProgress, SemesterResult, GradeAudit, UserProfile
)


# ==========================================================
# 🧭 STRUCTURE PÉDAGOGIQUE
# ==========================================================

@admin.register(MasterProgram)
class MasterProgramAdmin(admin.ModelAdmin):
    list_display = ("program", "code", "is_active", "default_ects_per_semester", "rattrapage_take_max")
    list_filter = ("is_active",)
    search_fields = ("program__title", "code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ("label", "start_date", "end_date")
    search_fields = ("label",)
    ordering = ("-start_date",)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("program", "cohort", "name", "order", "ects_target", "is_locked", "locked_by")
    list_filter = ("program", "cohort", "is_locked")
    search_fields = ("program__title", "cohort__label", "name")
    readonly_fields = ("locked_at",)


@admin.register(ModuleUE)
class ModuleUEAdmin(admin.ModelAdmin):
    list_display = ("semester", "code", "title", "coefficient", "credits", "is_active")
    list_filter = ("semester", "is_active")
    search_fields = ("code", "title")
    ordering = ("semester", "order")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("module", "title", "order", "is_locked")
    list_filter = ("module", "is_locked")
    search_fields = ("title", "module__title")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("chapter", "title", "is_published", "order", "duration_seconds")
    list_filter = ("chapter__module__semester", "is_published")
    search_fields = ("title", "chapter__title")


# ----- Ressources, Discussions & Quiz -----

@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    list_display = ("lesson", "title", "uploaded_at")
    search_fields = ("title", "lesson__title")


@admin.register(LessonDiscussion)
class LessonDiscussionAdmin(admin.ModelAdmin):
    list_display = ("lesson", "user", "created_at")
    list_filter = ("lesson__chapter__module__semester",)
    search_fields = ("lesson__title", "user__username", "message")
    ordering = ("-created_at",)


@admin.register(LessonQuiz)
class LessonQuizAdmin(admin.ModelAdmin):
    list_display = ("lesson", "title", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "lesson__title")


@admin.register(LessonQuizQuestion)
class LessonQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "text", "multiple_choice")
    search_fields = ("text", "quiz__lesson__title")


@admin.register(LessonQuizAnswer)
class LessonQuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "text", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text", "question__quiz__lesson__title")


# ==========================================================
# 👥 INSCRIPTIONS & AFFECTATIONS
# ==========================================================

@admin.register(MasterEnrollment)
class MasterEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "program", "cohort", "status", "created_at")
    list_filter = ("program", "cohort", "status")
    search_fields = ("student__username", "program__title", "cohort__label")


@admin.register(InstructorAssignment)
class InstructorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("instructor", "module", "role", "is_active")
    list_filter = ("role", "is_active", "module__semester")
    search_fields = ("instructor__username", "module__code", "module__title")


# ==========================================================
# 🧾 ÉVALUATIONS : DEVOIRS, EXAMENS, NOTES
# ==========================================================

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("module", "title", "eval_kind", "kind", "is_published", "open_at", "close_at")
    list_filter = ("module__semester", "eval_kind", "is_published")
    search_fields = ("title", "module__code", "description")
    date_hierarchy = "open_at"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "status", "note_20", "graded_by", "graded_at")
    list_filter = ("status", "assignment__module__semester")
    search_fields = ("assignment__title", "student__username")
    readonly_fields = ("graded_at",)
    date_hierarchy = "graded_at"


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("semester", "title", "eval_kind", "is_published", "start_at", "end_at")
    list_filter = ("semester", "eval_kind", "is_published")
    search_fields = ("title", "semester__name")


@admin.register(ExamGrade)
class ExamGradeAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "attempt_no", "note_20", "graded_at")
    list_filter = ("exam__semester",)
    search_fields = ("exam__title", "student__username")


# ==========================================================
# 📈 PROGRESSION ET RÉSULTATS
# ==========================================================

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "completed_at", "seconds_watched")
    list_filter = ("lesson__chapter__module__semester",)
    search_fields = ("lesson__title", "enrollment__student__username")


@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "module", "percent", "updated_at")
    list_filter = ("module__semester",)
    search_fields = ("module__title", "enrollment__student__username")


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "semester", "average_20", "credits_earned", "decision", "is_locked")
    list_filter = ("semester", "decision", "is_locked")
    search_fields = ("enrollment__student__username", "semester__name")


# ==========================================================
# 🕵️ AUDIT ET PROFIL UTILISATEUR
# ==========================================================

@admin.register(GradeAudit)
class GradeAuditAdmin(admin.ModelAdmin):
    list_display = ("actor", "context", "context_id", "created_at")
    search_fields = ("context", "context_id", "actor__username")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "must_change_password")
    list_filter = ("must_change_password",)
    search_fields = ("user__username",)
