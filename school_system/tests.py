from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import School, Grade, ClassRoom, Subject, TeacherProfile, StudentProfile

User = get_user_model()


class SchoolModelTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            code='SCH001',
            address='123 Test St',
            city='Gaza',
            phone='+970500000000',
            email='school@test.com',
        )

    def test_school_creation(self):
        self.assertEqual(self.school.name, 'Test School')
        self.assertEqual(str(self.school), 'Test School (SCH001)')


class GradeModelTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School', code='SCH001',
            address='Addr', city='Gaza', phone='123', email='a@b.com',
        )
        self.grade = Grade.objects.create(
            school=self.school, name='Grade 6',
            grade_level=6, academic_year='2025-2026',
        )

    def test_grade_creation(self):
        self.assertEqual(str(self.grade), 'SCH001 - Grade 6')


class ClassRoomModelTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School', code='SCH001',
            address='Addr', city='Gaza', phone='123', email='a@b.com',
        )
        self.grade = Grade.objects.create(
            school=self.school, name='Grade 6',
            grade_level=6, academic_year='2025-2026',
        )
        self.classroom = ClassRoom.objects.create(
            grade=self.grade, name='6-A', capacity=30,
        )

    def test_classroom_creation(self):
        self.assertEqual(str(self.classroom), 'Grade 6 - 6-A')


class SubjectModelTest(TestCase):
    def test_subject_creation(self):
        subject = Subject.objects.create(
            name='Mathematics', code='MATH101',
            category='MATH', is_core_subject=True,
        )
        self.assertEqual(str(subject), 'Mathematics (MATH101)')


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='teacher@test.com',
            username='teacher1',
            password='testpass123',
            role='TEACHER',
        )
        self.assertEqual(user.email, 'teacher@test.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='admin123',
        )
        self.assertTrue(admin.is_superuser)
