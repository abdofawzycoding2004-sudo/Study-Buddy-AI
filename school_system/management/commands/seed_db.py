from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from school_system.models import School, Grade, ClassRoom, Subject, TeacherProfile, StudentProfile
from teacher_panel.models import Course as TPCourse, Module as TPModule, Category as TPCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with example school data'

    def handle(self, *args, **options):
        if School.objects.exists():
            self.stdout.write(self.style.WARNING('Database already seeded. Skipping.'))
            return

        # ── School ──
        school = School.objects.create(
            name='Al-Madrasa Al-Namuzajiya',
            code='SCH001',
            address='Al-Rimal, Gaza',
            city='Gaza',
            country='Palestine',
            phone='+970 8 288 8888',
            email='info@namuzajiya.edu',
            established_date=date(2010, 9, 1),
        )
        self.stdout.write(f'Created school: {school}')

        # ── Subjects ──
        subjects_data = [
            ('Mathematics', 'MATH101', 'MATH', True),
            ('Physics', 'PHY201', 'SCIENCE', True),
            ('Chemistry', 'CHM301', 'SCIENCE', True),
            ('Arabic Language', 'ARB101', 'LANGUAGE', True),
            ('English Language', 'ENG101', 'LANGUAGE', True),
            ('Islamic Education', 'ISL101', 'SOCIAL_STUDIES', True),
            ('History', 'HIS101', 'SOCIAL_STUDIES', False),
            ('Geography', 'GEO101', 'SOCIAL_STUDIES', False),
            ('Physical Education', 'PED101', 'SPORTS', False),
            ('Art', 'ART101', 'ART', False),
        ]
        subjects = []
        for name, code, category, core in subjects_data:
            subj = Subject.objects.create(
                name=name, code=code, category=category,
                is_core_subject=core, description=f'{name} subject'
            )
            subj.schools.add(school)
            subjects.append(subj)
        self.stdout.write(f'Created {len(subjects)} subjects')

        # ── Grades ──
        grades = []
        for level in [6, 7, 8]:
            g = Grade.objects.create(
                school=school,
                name=f'Grade {level}',
                grade_level=level,
                academic_year='2025-2026',
            )
            grades.append(g)
        self.stdout.write(f'Created {len(grades)} grades')

        # ── Classes (3 per grade) ──
        sections = ['A', 'B', 'C']
        classrooms = []
        for g in grades:
            for sec in sections:
                cls = ClassRoom.objects.create(
                    grade=g,
                    name=f'{g.grade_level}-{sec}',
                    capacity=30,
                )
                classrooms.append(cls)
        self.stdout.write(f'Created {len(classrooms)} classrooms')

        # ── Teacher users + profiles ──
        teachers_data = [
            ('ahmad', 'Ahmad', 'Hassan', 'ahmad@school.edu', 'TCH001', 8, ['MATH101', 'PHY201']),
            ('sara', 'Sara', 'Mahmoud', 'sara@school.edu', 'TCH002', 6, ['ARB101', 'ISL101']),
            ('omar', 'Omar', 'Khalid', 'omar@school.edu', 'TCH003', 5, ['ENG101', 'HIS101']),
        ]
        teacher_profiles = []
        for username, first, last, email, eid, exp, subj_codes in teachers_data:
            user = User.objects.create_user(
                username=username, email=email,
                password='password123',
                first_name=first, last_name=last,
                role='teacher',
            )
            profile = TeacherProfile.objects.create(
                user=user,
                employee_id=eid,
                school=school,
                qualifications=f'Bachelor in {subj_codes[0]}',
                experience_years=exp,
                hire_date=date(2020, 9, 1),
            )
            profile.subjects.set(Subject.objects.filter(code__in=subj_codes))
            teacher_profiles.append(profile)
        self.stdout.write(f'Created {len(teacher_profiles)} teachers')

        # Set class teachers
        classrooms[0].class_teacher = teacher_profiles[0]  # 6-A
        classrooms[0].save()
        classrooms[3].class_teacher = teacher_profiles[1]  # 7-A
        classrooms[3].save()
        classrooms[6].class_teacher = teacher_profiles[2]  # 8-A
        classrooms[6].save()

        # ── Student users + profiles ──
        students_data = [
            # (username, first, last, email, student_id, grade_idx, class_idx, gender, parent)
            ('ali88', 'Ali', 'Omar', 'ali@student.edu', 'STU2025001', 0, 0, 'MALE', 'Omar Ahmad'),
            ('noor99', 'Noor', 'Hassan', 'noor@student.edu', 'STU2025002', 0, 0, 'FEMALE', 'Hassan Saleh'),
            ('layla22', 'Layla', 'Khaled', 'layla@student.edu', 'STU2025003', 0, 0, 'FEMALE', 'Khaled Mahmoud'),
            ('ahmed77', 'Ahmed', 'Ali', 'ahmed7@student.edu', 'STU2025004', 1, 3, 'MALE', 'Ali Yousef'),
            ('dina55', 'Dina', 'Sami', 'dina@student.edu', 'STU2025005', 1, 3, 'FEMALE', 'Sami Kamel'),
            ('yousef33', 'Yousef', 'Nabil', 'yousef@student.edu', 'STU2025006', 1, 3, 'MALE', 'Nabil Hani'),
            ('huda11', 'Huda', 'Ibrahim', 'huda@student.edu', 'STU2025007', 2, 6, 'FEMALE', 'Ibrahim Fathi'),
            ('kareem00', 'Kareem', 'Ziad', 'kareem@student.edu', 'STU2025008', 2, 6, 'MALE', 'Ziad Kamel'),
            ('rana88', 'Rana', 'Adel', 'rana@student.edu', 'STU2025009', 2, 6, 'FEMALE', 'Adel Mahdi'),
        ]
        students = []
        for username, first, last, email, sid, gi, ci, gender, parent in students_data:
            user = User.objects.create_user(
                username=username, email=email,
                password='password123',
                first_name=first, last_name=last,
                role='student',
            )
            student = StudentProfile.objects.create(
                user=user,
                student_id=sid,
                school=school,
                classroom=classrooms[ci],
                grade=grades[gi],
                date_of_birth=date(2012, 6, 15),
                gender=gender,
                parent_name=parent,
                parent_phone='+970 59 999 9999',
                emergency_contact_name=parent,
                emergency_contact_phone='+970 59 888 8888',
            )
            # update enrollment count
            classrooms[ci].current_enrollment += 1
            classrooms[ci].save()
            students.append(student)
        self.stdout.write(f'Created {len(students)} students')

        # ── Teacher Panel: Categories, Courses, Modules ──
        cat = TPCategory.objects.create(name='STEM')
        courses_data = [
            ('Mathematics — Grade 6', 'Basic arithmetic, algebra intro, geometry basics', teacher_profiles[0]),
            ('Arabic Language — Grade 7', 'Grammar, literature, writing composition', teacher_profiles[1]),
            ('English Language — Grade 8', 'Reading comprehension, grammar, vocabulary', teacher_profiles[2]),
        ]
        for title, desc, teacher in courses_data:
            course = TPCourse.objects.create(
                title=title,
                description=desc,
                created_by=teacher.user,
                category=cat,
            )
            TPModule.objects.create(course=course, title=f'Introduction', order=1, description='Overview and basics')
            TPModule.objects.create(course=course, title=f'Core Topics', order=2, description='Main subject content')
            TPModule.objects.create(course=course, title=f'Revision', order=3, description='Review and practice')
        self.stdout.write(f'Created {len(courses_data)} courses with modules')

        # ── Superuser ──
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin', email='admin@admin.com',
                password='admin',
            )
            self.stdout.write('Created superuser: admin / admin')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
