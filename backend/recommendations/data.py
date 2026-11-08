"""Learning resources and general study ideas."""

RESOURCES = {
    "python": ("General-purpose language used for web, data and automation.", 6, [
        ("Official Python Tutorial", "https://docs.python.org/3/tutorial/"),
        ("freeCodeCamp: Python course (YouTube)", "https://www.youtube.com/@freecodecamp"),
        ("Kaggle Learn: Python", "https://www.kaggle.com/learn/python")]),
    "django": ("Python web framework for building secure backends and APIs quickly.", 6, [
        ("Official Django tutorial", "https://docs.djangoproject.com/en/stable/intro/tutorial01/"),
        ("Django REST Framework docs", "https://www.django-rest-framework.org/tutorial/quickstart/"),
        ("MDN Django tutorial", "https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django")]),
    "flask": ("Lightweight Python web framework, good for small APIs.", 3, [
        ("Flask tutorial", "https://flask.palletsprojects.com/en/stable/tutorial/")]),
    "javascript": ("The language of the browser; required for any interactive website.", 6, [
        ("MDN JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
        ("javascript.info", "https://javascript.info/"),
        ("freeCodeCamp curriculum", "https://www.freecodecamp.org/learn/")]),
    "typescript": ("JavaScript with types; common in larger React/Node teams.", 3, [
        ("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html")]),
    "react": ("Most popular library for building user interfaces.", 6, [
        ("react.dev Learn", "https://react.dev/learn"),
        ("Scrimba: Learn React (free)", "https://scrimba.com/learn/learnreact")]),
    "node.js": ("JavaScript on the server for APIs and tooling.", 4, [
        ("Node.js Learn", "https://nodejs.org/en/learn"),
        ("The Odin Project: NodeJS", "https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs")]),
    "html": ("The structure of every web page.", 2, [
        ("MDN: Learn HTML", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content"),
        ("web.dev Learn HTML", "https://web.dev/learn/html")]),
    "css": ("Styling and responsive layout for the web.", 3, [
        ("web.dev Learn CSS", "https://web.dev/learn/css"),
        ("MDN: CSS first steps", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics")]),
    "sql": ("Query and design relational databases (MySQL, PostgreSQL).", 3, [
        ("SQLBolt interactive lessons", "https://sqlbolt.com/"),
        ("Mode SQL tutorial", "https://mode.com/sql-tutorial/"),
        ("Kaggle Learn: Intro to SQL", "https://www.kaggle.com/learn/intro-to-sql")]),
    "mongodb": ("Popular NoSQL document database.", 3, [
        ("MongoDB University (free)", "https://learn.mongodb.com/")]),
    "php": ("Server-side language behind WordPress and Laravel; common in Nepal.", 6, [
        ("PHP manual: Getting started", "https://www.php.net/manual/en/getting-started.php"),
        ("Laravel documentation", "https://laravel.com/docs")]),
    "java": ("Typed, enterprise-grade language for backends and Android.", 8, [
        ("dev.java Learn", "https://dev.java/learn/")]),
    "c++": ("Systems language; strong for algorithms and performance.", 8, [
        ("learncpp.com", "https://www.learncpp.com/")]),
    "flutter": ("Build Android and iOS apps from one Dart codebase.", 6, [
        ("Flutter documentation & codelabs", "https://docs.flutter.dev/get-started/codelab"),
        ("Dart language tour", "https://dart.dev/language")]),
    "laravel": ("Popular PHP framework; many Nepali agencies hire for it.", 6, [
        ("Laravel documentation", "https://laravel.com/docs"),
        ("Laravel Bootcamp", "https://bootcamp.laravel.com/")]),
    "wordpress": ("Most used website platform; steady freelance and agency work.", 4, [
        ("Learn WordPress (official)", "https://learn.wordpress.org/")]),
    "figma": ("Design tool for app and website screens.", 3, [
        ("Figma Learn Design", "https://www.figma.com/resources/learn-design/")]),
    "ui/ux design": ("Designing screens that are easy and pleasant to use.", 8, [
        ("Google UX Design Certificate (Coursera, financial aid available)", "https://www.coursera.org/professional-certificates/google-ux-design"),
        ("Interaction Design Foundation articles", "https://www.interaction-design.org/literature")]),
    "graphic design": ("Posters, social media and brand visuals.", 6, [
        ("Canva Design School", "https://www.canva.com/designschool/")]),
    "video editing": ("Editing reels, ads and tutorials.", 6, [
        ("DaVinci Resolve free training", "https://www.blackmagicdesign.com/products/davinciresolve/training")]),
    "digital marketing": ("SEO, social media and ads; in demand at Nepali startups and agencies.", 6, [
        ("Google Digital Garage", "https://learndigital.withgoogle.com/digitalgarage"),
        ("HubSpot Academy (free courses)", "https://academy.hubspot.com/")]),
    "content writing": ("Writing blogs, captions and website copy.", 4, [
        ("HubSpot Academy: Content Marketing", "https://academy.hubspot.com/courses/content-marketing")]),
    "accounting": ("Bookkeeping, VAT and Tally; needed in every business.", 8, [
        ("AccountingCoach (free lessons)", "https://www.accountingcoach.com/"),
        ("Tally learning hub", "https://tallysolutions.com/learning-hub/")]),
    "sales": ("Finding and closing customers.", 4, [
        ("HubSpot Academy: Sales", "https://academy.hubspot.com/courses/sales")]),
    "customer service": ("Helping customers by phone, chat and email.", 3, [
        ("HubSpot Academy: Customer Service", "https://academy.hubspot.com/courses/customer-service")]),
    "project management": ("Planning work, teams and deadlines (Scrum, Agile).", 4, [
        ("The Scrum Guide", "https://scrumguides.org/"),
        ("Atlassian Agile Coach", "https://www.atlassian.com/agile")]),
    "ms office": ("Word, Excel and PowerPoint for everyday office work.", 3, [
        ("Microsoft Support training", "https://support.microsoft.com/en-us/training")]),
    "linux": ("Command line and servers; the base of most hosting.", 4, [
        ("Linux Journey", "https://linuxjourney.com/")]),
    "networking": ("How networks work: IP, routing, switching.", 8, [
        ("Cisco Networking Academy", "https://www.netacad.com/")]),
    "cybersecurity": ("Protecting systems and data.", 10, [
        ("TryHackMe (guided labs)", "https://tryhackme.com/")]),
    "devops": ("Automating build, test and deployment.", 8, [
        ("roadmap.sh DevOps path", "https://roadmap.sh/devops")]),
    "vue": ("Friendly JavaScript framework for interfaces.", 4, [
        ("Vue tutorial", "https://vuejs.org/tutorial/")]),
    "angular": ("Google's framework for large web apps.", 6, [
        ("Angular tutorials", "https://angular.dev/tutorials")]),
    "next.js": ("React framework for fast, SEO-friendly sites.", 3, [
        ("Learn Next.js", "https://nextjs.org/learn")]),
    "react native": ("Build mobile apps with React.", 6, [
        ("React Native docs", "https://reactnative.dev/docs/getting-started")]),
    "android": ("Native Android apps with Kotlin.", 8, [
        ("Android Developers courses", "https://developer.android.com/courses")]),
    "ios": ("Apple apps with Swift and SwiftUI.", 8, [
        ("SwiftUI tutorials", "https://developer.apple.com/tutorials/swiftui")]),
    "c#": ("Microsoft language for .NET backends and games.", 8, [
        ("C# docs (Microsoft Learn)", "https://learn.microsoft.com/en-us/dotnet/csharp/")]),
    "spring boot": ("Java framework for production backends.", 8, [
        ("Spring guides", "https://spring.io/guides")]),
    "firebase": ("Google's backend for mobile and web apps.", 3, [
        ("Firebase documentation", "https://firebase.google.com/docs")]),
    "git": ("Version control; every team expects it.", 1, [
        ("Pro Git book (free)", "https://git-scm.com/book/en/v2"),
        ("GitHub Skills", "https://skills.github.com/")]),
    "docker": ("Package apps into containers so they run the same everywhere.", 2, [
        ("Docker Get Started", "https://docs.docker.com/get-started/")]),
    "aws": ("Leading cloud platform; hosting, storage, databases.", 6, [
        ("AWS Skill Builder (free tier)", "https://skillbuilder.aws/"),
        ("AWS Cloud Practitioner Essentials", "https://aws.amazon.com/training/")]),
    "rest api": ("Designing and consuming HTTP APIs, the glue between frontend and backend.", 2, [
        ("restfulapi.net", "https://restfulapi.net/"),
        ("Django REST Framework quickstart", "https://www.django-rest-framework.org/tutorial/quickstart/")]),
    "machine learning": ("Training models that learn from data.", 12, [
        ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
        ("Kaggle Learn: Intro to ML", "https://www.kaggle.com/learn/intro-to-machine-learning"),
        ("scikit-learn user guide", "https://scikit-learn.org/stable/user_guide.html")]),
    "data analysis": ("Cleaning, exploring and presenting data (Excel, pandas, Power BI).", 6, [
        ("Kaggle Learn: Pandas", "https://www.kaggle.com/learn/pandas"),
        ("Kaggle Learn: Data Visualization", "https://www.kaggle.com/learn/data-visualization"),
        ("Microsoft Learn: Power BI", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi")]),
    "testing": ("Finding bugs systematically: manual, automated and unit tests.", 4, [
        ("Test Automation University (free)", "https://testautomationu.com/"),
        ("Selenium documentation", "https://www.selenium.dev/documentation/"),
        ("pytest getting started", "https://docs.pytest.org/en/stable/getting-started.html")]),
    "communication": ("Clear writing, teamwork and presenting your work.", 4, [
        ("Toastmasters", "https://www.toastmasters.org/"),
        ("Write a project README or blog post for every project you build", "https://www.freecodecamp.org/news/")]),
}


GENERAL_IDEAS = [
    "Build 2-3 small projects that use the skills you are learning and publish them on GitHub.",
    "Follow a structured path on roadmap.sh (https://roadmap.sh/) so you know what comes next.",
    "Contribute to a small open-source project or build something for a local business or your campus.",
    "Look for internships, freelance gigs or volunteer work in Kathmandu, Lalitpur or Pokhara tech companies to gain experience.",
]


def resources_for(skill):
    info = RESOURCES.get(skill)
    if info:
        why, weeks, links = info
        return why, weeks, [{"label": l, "url": u} for l, u in links]
    q = skill.replace(" ", "+")
    return (
        f"Required by employers on JobMitra for {skill}.",
        4,
        [
            {"label": f"Search free {skill} courses on YouTube", "url": f"https://www.youtube.com/results?search_query=learn+{q}+full+course"},
            {"label": "roadmap.sh learning paths", "url": "https://roadmap.sh/"},
        ],
    )
