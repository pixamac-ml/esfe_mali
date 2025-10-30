# masters/models.py
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL


# ==========================================================
# CONSTANTES GLOBALES
# ==========================================================

CYCLE_MASTER = "MASTER"

EVAL_KIND = (
    ("CC", "Contrôle Continu"),
    ("TP", "Travaux Pratiques"),
    ("EX", "Examen / Partiel"),
    ("FN", "Final"),
    ("RA", "Rattrapage"),
)

ASSIGNMENT_KIND = (
    ("QCM", "QCM"),
    ("DM", "Devoir Maison"),
    ("PRJ", "Projet"),
    ("CAS", "Étude de cas"),
)

SUBMISSION_STATUS = (
    ("DRAFT", "Brouillon"),
    ("SUBMITTED", "Soumis"),
    ("GRADED", "Noté"),
    ("LATE", "En retard"),
)

ENROLL_STATUS = (
    ("ACTIVE", "Actif"),
    ("SUSPENDED", "Suspendu"),
    ("WITHDRAWN", "Abandonné"),
    ("COMPLETED", "Terminé"),
)

DECISION = (
    ("ADM", "Admis"),
    ("AJ", "Ajourné"),
    ("RAT", "Rattrapage"),
    ("EXC", "Exclu"),
)

INSTRUCTOR_ROLE = (
    ("LEAD", "Responsable UE"),
    ("ASSIST", "Assistant"),
)

NOTE_MIN = 0.0
NOTE_MAX = 20.0


# ==========================================================
# MASTER PROGRAMMES
# ==========================================================

class MasterProgram(models.Model):
    """Métadonnées spécifiques Master, enveloppant un Program existant (cycle=MASTER)."""
    program = models.OneToOneField(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="master_meta",
        limit_choices_to={"cycle": CYCLE_MASTER},
    )
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    default_ects_per_semester = models.PositiveSmallIntegerField(
        default=30, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    rattrapage_take_max = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.program.title} [{self.code}]"


# ==========================================================
# COHORTES & SEMESTRES
# ==========================================================

class Cohort(models.Model):
    label = models.CharField(max_length=32, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.label


class Semester(models.Model):
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        limit_choices_to={"cycle": CYCLE_MASTER},
        related_name="master_semesters",
    )
    cohort = models.ForeignKey(Cohort, on_delete=models.PROTECT, related_name="semesters")
    name = models.CharField(max_length=32)
    order = models.PositiveSmallIntegerField(default=1)
    ects_target = models.PositiveSmallIntegerField(default=30)
    is_unlocked_by_default = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="locked_semesters"
    )

    class Meta:
        ordering = ["program_id", "cohort_id", "order"]
        unique_together = (("program", "cohort", "name"),)

    def __str__(self):
        return f"{self.program.title} • {self.cohort} • {self.name}"

    def lock(self, by_user):
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.locked_by = by_user
            self.save(update_fields=["is_locked", "locked_at", "locked_by"])


# ==========================================================
# STRUCTURE PÉDAGOGIQUE : UE → Chapitres → Leçons
# ==========================================================

class ModuleUE(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="modules")
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    credits = models.DecimalField(max_digits=4, decimal_places=1, default=6.0)
    order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["semester_id", "order", "id"]
        unique_together = (("semester", "code"),)

    def __str__(self):
        return f"{self.semester} • {self.code} — {self.title}"


class Chapter(models.Model):
    module = models.ForeignKey(ModuleUE, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    is_locked = models.BooleanField(default=False, help_text="Chapitre bloqué avant validation préalable.")

    class Meta:
        ordering = ["module_id", "order", "id"]
        unique_together = (("module", "slug"),)

    def __str__(self):
        return f"{self.module.code} • {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=1)
    duration_seconds = models.PositiveIntegerField(default=0)
    video_file = models.FileField(upload_to="masters/videos/", blank=True)
    external_url = models.URLField(blank=True)
    resource_file = models.FileField(upload_to="masters/resources/", blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["chapter_id", "order", "id"]

    def __str__(self):
        return f"{self.chapter.module.code} • {self.title}"


# ==========================================================
# 🆕 ENRICHISSEMENTS : Ressources, Discussions, Quiz
# ==========================================================

class LessonResource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="masters/resources/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} • {self.title}"


class LessonDiscussion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="discussions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_messages")
    message = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.lesson.title}"


class LessonQuiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"Quiz: {self.lesson.title}"


class LessonQuizQuestion(models.Model):
    quiz = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)
    multiple_choice = models.BooleanField(default=False)

    def __str__(self):
        return f"Q{self.order} • {self.quiz.lesson.title}"


class LessonQuizAnswer(models.Model):
    question = models.ForeignKey(LessonQuizQuestion, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.quiz.lesson.title} → {self.text}"


# ==========================================================
# INSCRIPTIONS & AFFECTATIONS
# ==========================================================

class MasterEnrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="master_enrollments")
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="master_enrollments",
        limit_choices_to={"cycle": CYCLE_MASTER},
    )
    cohort = models.ForeignKey(Cohort, on_delete=models.PROTECT, related_name="enrollments")
    admission = models.OneToOneField("admissions.Admission", on_delete=models.PROTECT, related_name="master_enrollment")
    status = models.CharField(max_length=12, choices=ENROLL_STATUS, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("student", "program", "cohort"),)
        indexes = [models.Index(fields=["student", "program", "cohort"])]

    def __str__(self):
        return f"{self.student} → {self.program.title} ({self.cohort})"


class InstructorAssignment(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="master_teachings")
    module = models.ForeignKey(ModuleUE, on_delete=models.CASCADE, related_name="instructors")
    role = models.CharField(max_length=8, choices=INSTRUCTOR_ROLE, default="LEAD")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("instructor", "module"),)
        indexes = [models.Index(fields=["module", "instructor"])]

    def __str__(self):
        return f"{self.instructor} → {self.module.code} ({self.role})"


# ==========================================================
# DEVOIRS, SOUMISSIONS, EXAMENS, NOTES
# ==========================================================

class Assignment(models.Model):
    module = models.ForeignKey(ModuleUE, on_delete=models.CASCADE, related_name="assignments")
    chapter = models.ForeignKey(Chapter, null=True, blank=True, on_delete=models.SET_NULL, related_name="assignments")
    kind = models.CharField(max_length=4, choices=ASSIGNMENT_KIND, default="QCM")
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    open_at = models.DateTimeField(null=True, blank=True)
    close_at = models.DateTimeField(null=True, blank=True)
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=20.0)
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    eval_kind = models.CharField(max_length=2, choices=EVAL_KIND, default="CC")
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="created_assignments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["module_id", "open_at", "id"]

    def __str__(self):
        return f"{self.module.code} • {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="master_submissions")
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=SUBMISSION_STATUS, default="DRAFT")
    uploaded_file = models.FileField(upload_to="masters/submissions/", blank=True)
    answer_text = models.TextField(blank=True)
    score_raw = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True)
    note_20 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    graded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="graded_submissions")
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = (("assignment", "student"),)

    def __str__(self):
        return f"{self.assignment} ← {self.student}"

    def compute_note_20(self) -> Optional[float]:
        if self.score_raw is None:
            return None
        total = float(self.assignment.total_points)
        if total <= 0:
            return None
        note = (float(self.score_raw) / total) * 20.0
        return round(max(NOTE_MIN, min(NOTE_MAX, note)), 2)


class Exam(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=220, blank=True)
    eval_kind = models.CharField(max_length=2, choices=EVAL_KIND, default="EX")
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=20.0)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["semester_id", "start_at", "id"]

    def __str__(self):
        return f"{self.semester} • {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)


class ExamGrade(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="master_exam_grades")
    attempt_no = models.PositiveSmallIntegerField(default=1)
    score_raw = models.DecimalField(max_digits=7, decimal_places=3)
    note_20 = models.DecimalField(max_digits=4, decimal_places=2)
    graded_at = models.DateTimeField(auto_now_add=True)
    validated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="validated_exam_grades")

    class Meta:
        unique_together = (("exam", "student", "attempt_no"),)


# ==========================================================
# PROGRESSION ET RESULTATS
# ==========================================================

class LessonProgress(models.Model):
    enrollment = models.ForeignKey(MasterEnrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed_at = models.DateTimeField(null=True, blank=True)
    seconds_watched = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("enrollment", "lesson"),)


class ModuleProgress(models.Model):
    enrollment = models.ForeignKey(MasterEnrollment, on_delete=models.CASCADE, related_name="module_progress")
    module = models.ForeignKey(ModuleUE, on_delete=models.CASCADE, related_name="progress")
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("enrollment", "module"),)


class SemesterResult(models.Model):
    enrollment = models.ForeignKey(MasterEnrollment, on_delete=models.CASCADE, related_name="semester_results")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="results")
    average_20 = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    credits_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    decision = models.CharField(max_length=3, choices=DECISION, null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="locked_results")
    computed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("enrollment", "semester"),)

    def __str__(self):
        return f"{self.enrollment} • {self.semester} → {self.average_20 or '-'}"


class GradeAudit(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    context = models.CharField(max_length=32)
    context_id = models.CharField(max_length=64)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# ==========================================================
# PROFIL UTILISATEUR (mot de passe forcé)
# ==========================================================

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=True)

    def __str__(self):
        return f"Profil de {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# ==========================================================
# SIGNALS GLOBAUX
# ==========================================================

@receiver(pre_save, sender=Submission)
def _submission_pre_save(sender, instance: Submission, **kwargs):
    if instance.score_raw is not None and (instance.note_20 is None):
        instance.note_20 = instance.compute_note_20()
    if instance.note_20 is not None:
        instance.note_20 = round(max(NOTE_MIN, min(NOTE_MAX, float(instance.note_20))), 2)
