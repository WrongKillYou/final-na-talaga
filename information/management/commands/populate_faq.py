# information/management/commands/populate_faq.py
# Run with: python manage.py populate_faq

"""
PURPOSE OF THIS COMMAND:
========================
This management command populates your database with predefined FAQ responses
for the KinderCare chatbot assistant. 

WHY IT'S NEEDED:
- The chatbot needs questions and answers stored in the database
- Instead of manually adding 10+ FAQs through Django admin, this command does it automatically
- It creates BotMessage entries that the chatbot uses to respond to parents

WHEN TO USE:
- After first installation of the chat system
- When you want to reset/update FAQ responses
- When deploying to a new server/environment

HOW IT WORKS:
1. Creates/updates BotMessage records in the database
2. Each FAQ has keywords that trigger the response
3. The chatbot searches these keywords to find matching answers
4. If no match is found, bot offers to connect parent with a teacher

EXAMPLE:
- Parent types: "How do I enroll?"
- Bot searches keywords: "enrollment, enroll, requirements..."
- Bot finds match and responds with enrollment requirements
"""

from django.core.management.base import BaseCommand
from information.models import BotMessage


class Command(BaseCommand):
    help = 'Populate the database with FAQ bot messages for KinderCare Assistant'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating FAQ bot messages...')

        faqs = [
            {
                'category': 'enrollment',
                'keywords': 'enrollment, enroll, requirements, register, registration, admission, apply',
                'response_text': 'To enroll your child, you need: Birth Certificate, Immunization Records, 2x2 ID Photos (4pcs), Health Certificate, and filled-out enrollment form. Please visit our office during enrollment period.',
                'priority': 10
            },
            {
                'category': 'schedule',
                'keywords': 'schedule, time, hours, class time, school hours, what time',
                'response_text': 'Our kindergarten classes run from 8:00 AM to 12:00 PM, Monday to Friday. Extended care is available until 3:00 PM for working parents.',
                'priority': 9
            },
            {
                'category': 'attendance',
                'keywords': 'attendance, absent, absence, miss class, tardy, late',
                'response_text': 'Regular attendance is important for your child\'s development. Please notify us if your child will be absent. Excused absences require a parent note or medical certificate.',
                'priority': 8
            },
            {
                'category': 'health',
                'keywords': 'sick, illness, fever, health, medical, medicine, disease',
                'response_text': 'Please keep your child at home if they have fever, cough, or any contagious illness. They may return 24 hours after symptoms subside. Always inform the teacher about any medical conditions.',
                'priority': 10
            },
            {
                'category': 'contact',
                'keywords': 'contact, phone, email, address, location, office, reach',
                'response_text': 'You can reach us at: Phone: (+63) 0945-529-xxxx, Email: anonasdaycarecenter@school.edu.ph, Office Hours: Monday-Friday, 7:30 AM - 4:30 PM',
                'priority': 7
            },
            {
                'category': 'records',
                'keywords': 'progress, report, records, grades, performance, competency, assessment',
                'response_text': 'You can view your child\'s competency records and attendance through your parent dashboard. Reports are updated quarterly and you\'ll receive notifications when new assessments are posted.',
                'priority': 8
            },
            {
                'category': 'general',
                'keywords': 'bring, supplies, things, items, bag, uniform, clothes',
                'response_text': 'Your child should bring: Clean uniform, Snack and water bottle, Extra clothes, Handkerchief/tissue, School bag. Please label all items with your child\'s name.',
                'priority': 6
            },
            {
                'category': 'enrollment',
                'keywords': 'payment, tuition, fee, pay, cost, price, how much',
                'response_text': 'We do not charge tuition fees! However, some payments can be incurred to aid the learning development of your child, such as purchase of books and learning materials.',
                'priority': 7
            },
            {
                'category': 'general',
                'keywords': 'cancel, cancellation, suspension, no class, typhoon, holiday',
                'response_text': 'Classes are cancelled during typhoons, holidays, and emergencies. We will send announcements through the parent portal and SMS. Make-up classes will be scheduled as needed.',
                'priority': 6
            },
            {
                'category': 'contact',
                'keywords': 'update, change, contact information, phone number, address, email',
                'response_text': 'You can update your contact information through your Profile page or visit the school office. It\'s important to keep your contact details current for emergency situations.',
                'priority': 5
            },
            {
                'category': 'greeting',
                'keywords': 'hello, hi, hey, good morning, good afternoon, good evening',
                'response_text': 'Hello! 👋 Welcome to KinderCare. How can I assist you today? You can select a question below or type your concern.',
                'priority': 10
            },
            {
                'category': 'faq',
                'keywords': 'help, assist, question, ask, support, need, concern',
                'response_text': 'I\'m here to help! You can ask me about enrollment, schedules, attendance, health policies, contact information, progress reports, and more. What would you like to know?',
                'priority': 9
            },
            {
                'category': 'general',
                'keywords': 'thank, thanks, thank you, appreciate',
                'response_text': 'You\'re welcome! Is there anything else I can help you with today?',
                'priority': 5
            },
        ]

        created_count = 0

        for faq_data in faqs:
            # Create new FAQ
            BotMessage.objects.create(
                **faq_data,
                is_active=True,
                has_buttons=False,
                usage_count=0
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created: {faq_data["category"]} - {faq_data["keywords"][:50]}...')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully populated {created_count} FAQ messages for Anonas Day Care Center'
            )
        )