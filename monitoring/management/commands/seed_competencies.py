from django.core.management.base import BaseCommand
from monitoring.models import Domain, Competency

class Command(BaseCommand):
    help = 'Seed default domains and competencies for the Kindergarten Framework'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding default domains and competencies...')

        # List of domains and their competencies
        framework = [
            {
                'name': 'Health, Well-Being, and Motor Development',
                'description': 'Competencies related to personal health and motor skills.',
                'competencies': [
                    "Demonstrates health habits that keep one clean and sanitary",
                    "Demonstrates behaviors that promote personal safety",
                    "Demonstrates locomotor skills such as walking, running, skipping, jumping, climbing correctly during play, dance or exercise activities",
                    "Demonstrates non-locomotor skills such as pushing, pulling, turning, swaying, bending, throwing, catching, and kicking correctly during play, dance or exercise activities",
                    "Demonstrates fine motor skills needed for self-care / self-help such as tooth brushing, buttoning, screwing and unscrewing lids, using spoon and fork correctly, etc.",
                    "Demonstrates fine motor skills needed for creative self-expression/ art activities, such as tearing, cutting, pasting, copying, drawing, coloring, molding, painting, lacing, etc.",
                    "Traces, copies, or writes letters and numerals"
                ]
            },
            {
                'name': 'Socio-Emotional Development',
                'description': 'Competencies related to social-emotional skills.',
                'competencies': [
                    "States personal information (name, gender, age, birthday)",
                    "Expresses personal interests and needs",
                    "Demonstrates readiness in trying out new experiences, and self-confidence in doing tasks independently",
                    "Expresses feelings in appropriate ways and in different situations",
                    "Follows school rules willingly and executes school tasks and routines well",
                    "Recognizes different emotions, acknowledges the feelings of others, and shows willingness to help",
                    "Shows respect in dealing with peers and adults",
                    "Identifies members of one's family",
                    "Identifies people and places in the school and community"
                ]
            },
            {
                'name': 'Language, Literacy, and Communication',
                'description': 'Listening, speaking, reading, and writing skills.',
                'competencies': [
                    # Listening & Viewing
                    "Distinguishes between elements of sounds e.g. pitch (low and high), volume (loud and soft)",
                    "Listens attentively to stories/poems/songs",
                    "Recalls details from stories/poems/songs listened to",
                    "Relate story events to personal experiences",
                    "Sequence events from a story listened to",
                    "Infer character traits and feelings",
                    "Identify simple cause-and-effect and problem-solution relationship of events in a story listened to or in a familiar situation",
                    "Predict story outcomes",
                    "Discriminates objects/pictures as same and different, identifies missing parts of objects/pictures, and identifies which objects do not belong to the group",
                    # Speaking
                    "Uses proper expressions in and polite greetings in appropriate situations",
                    "Talks about details of objects, people, etc. using appropriate speaking vocabulary",
                    "Participates actively in class activities (e.g., reciting poems, rhymes, etc.) and discussions by responding to questions accordingly",
                    "Asks simple questions(who, what, where, when, why)",
                    "Gives 1 to 2 step directions",
                    "Retells simple stories or narrates personal experiences",
                    # Reading
                    "Identifies sounds of letters (using the alphabet of the Mother Tongue)",
                    "Names uppercase and lower case letters (using the alphabet of the Mother Tongue)",
                    "Matches uppercase and lower case letters (using the alphabet of the Mother Tongue)",
                    "Identifies beginning sound of a given word",
                    "Distinguishes words that rhyme",
                    "Counts syllables in a given word",
                    "Identifies parts of the book (front and back, title, author, illustrator, etc.)",
                    "Shows interest in reading by browsing through books, predicting what the story is all about and demonstrating proper book handling behavior (e.g., flip pages sequentially, browses from left to right, etc.)",
                    "Interprets information from simple pictographs, maps, and other environmental print",
                    # Writing
                    "Writes one's given name",
                    "Writes lower case and upper case letters",
                    "Express simple ideas through symbols (e.g., drawings, invented spelling)"
                ]
            },
            {
                'name': 'Mathematics',
                'description': 'Numeracy and problem-solving skills.',
                'competencies': [
                    "Identifies colors",
                    "Identifies shapes",
                    "Sorts objects according to shape, size, and/or color",
                    "Compares and arrange objects according to a specific attribute (e.g., size, length, quantity, or duration)",
                    "Recognizes and extends patterns",
                    "Tells the names of days in a week",
                    "Tells the months of the year",
                    "Distinguishes the time of day and tells time by the hour (using analog clock)",
                    "Rote counts up to 20",
                    "Counts objects up to 10",
                    "Recognize numerals up to 10",
                    "Writes numerals up 10",
                    "Sequences numbers",
                    "Identify the placement of objects (e.g. 1st, 2nd, 3rd, etc.) in a given set",
                    "Solves simple addition problems",
                    "Solves simple subtractions problems",
                    "Groups sets of concrete objects of equal quantities up to 10 (i.e., beginning multiplication)",
                    "Separates sets of concrete objects of equal quantities up to 10 (i.e., beginning division)",
                    "Measures length, capacity, and mass of objects using nonstandard measuring tools",
                    "Recognizes coins and bills (up to PHP 20)"
                ]
            },
            {
                'name': 'Understanding the Physical and Natural Environment',
                'description': 'Basic science and environmental skills.',
                'competencies': [
                    "Identifies body parts and their functions",
                    "Records observations and data with pictures, numbers and/or symbols",
                    "Identifies parts of plant and animals",
                    "Classifies animals according to shared characteristics",
                    "Describes the basic needs and ways to care for plants, animals and the environment",
                    "Identify different kinds of weather"
                ]
            }
        ]

        # Seed domains and competencies
        for domain_order, d in enumerate(framework, start=1):
            domain, created = Domain.objects.get_or_create(
                name=d['name'],
                defaults={'description': d['description'], 'order': domain_order}
            )
            for comp_order, desc in enumerate(d['competencies'], start=1):
                code = f"{domain.name[:2].upper()}{comp_order}"
                Competency.objects.get_or_create(
                    domain=domain,
                    code=code,
                    defaults={'description': desc, 'order': comp_order}
                )

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
