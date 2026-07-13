# Los Energúmenos
Repository of the final project for the Software Engineering II course in the 2026-I semester.

## Members
- Joan Camilo Betancourt Gonzalez (jobetancourtg@unal.edu.co)
- Raúl Felipe Rodríguez Hernández (rrodriguezhe@unal.edu.co)
- David Eduardo Calderón Parra (dcalderonpa@unal.edu.co)
- Sergio Andrés Hernández Salinas (serhernandezsa@unal.edu.co)
- Daniel Oñate Hernández (donateh@unal.edu.co)

## Content
In this repository you will find two folders:
- Deliveries: Folder dedicated solely to documents related to analysis and design.
- Final-Project: Folder dedicated to the application's source code, in it you will find all source files, scripts, diagrams, and documentation.

## Project: Mewtual ![Badge in Development](https://img.shields.io/badge/STATUS-IN%20DEVELOPMENT-green)
<p align="center">
<img width="500" height="500" alt="image" src="https://github.com/rrodriguezhe/mewtual/blob/976109b93dc99dd3f211e5667cf7d924ce28c166/Logo%20Mewtual.png" />
</p>

Finding the ideal mate for our pets and carrying out a controlled and safe breeding process is difficult these days. Although informal social networks or personal contacts are used to find feline pairings, information is scattered, unverified, and coordination often becomes unsafe and ineffective. Not only is finding compatibility and genetic characteristics difficult, but verifying the health and responsibility of the owners also becomes risky, as there are no tools to centralize medical records and facilitate ethical pairings to provide a reliable experience for those seeking their pet's well-being. This results in uninformed breedings, health problems, and even difficulties in rehoming the kittens.

Therefore, we propose creating an application within the PetTech sector that functions as an interactive social network, compatibility filter, and support community to facilitate responsible pairings, verify vaccination histories, and manage litter adoptions: an owner creates a detailed profile of their cat and browses for mates, as well as being able to arrange meetings and post kittens for adoption or as a gift.

Additionally, Mewtual differentiates itself from other pet communities by moving beyond informality, allowing users to filter ideal matches through a swipe-type matching system. Furthermore, it integrates a direct chat and health verification to connect only with responsible owners, ensuring that the breeding process is not only safer, more efficient, and more informed, but also guaranteeing the well-being and a reliable future home for each feline.

## Structure 🧱⚙️
Mewtual follows a Modular Monolith architecture using Django as the web framework. The application is organized into independent Django apps, each responsible for a specific domain of the system. This approach provides clear separation of concerns while keeping deployment simple.

There are 7 apps or modules that we work with that handle different tasks:
- users: Responsible for the registration process, login, user profiles.
- cats: Responsible for managing cat profiles.
- matching: Responsible for swipe logic and match generation.
- chat: Responsible for managing chats and messages between users who have matched.
- appointments: Responsible for scheduling and confirming appointments between cat owners.
- adoption: Responsible for the adoption or gift publication process, as well as its traceability.
- reports: Responsible for handling reports between users.

Each of these apps contains different files that handle: model logic for connecting to the database, serializers to manage a REST API that allows information to be entered correctly, functionality tests, URLs to define routing between tabs, views as functions to receive data from forms and route through the views, and finally the templates that are our frontend made in HTML.

## Setup 💻🛠️

**Prerequisites:**
- Python 3.10 or higher
- Docker and Docker compose
- Git

**Instructions for setup:**  

1. Clone the repository locally
2. Configure local variables in a .env file
3. Open Docker Desktop
4. Run the docker-compose.yml file
5. Install the Python dependencies:  
```pip install -r requirements.txt```  
6. Create a virtual environment with Python:  
```python -m venv venv```  
7. Start the virtual environment by running the file:  
```Activate.ps1```  
that is within the virtual environment.  
8. Install Django:  
```pip install django```  
9. Create local database migrations using:  
```python manage.py migrate```

In order to see more detailed all the setup steps, visit the Final-Project/Documentation directory in the repository.

## Usage 🕵️📍
To use the application, simply run the server with the following command:

<p align="center">
python manage.py runserver
</p>

After this, a message will appear in the terminal which gives a URL with which you can access the web page.
Finally, open this http in your preferred browser and use the page locally with all its features. 🤗✅

## Testing 🔍🔦
**Linter Testing with Flake8**

Activate the virtual environment and navigate to the backend/ folder.
Install Flake8:

```pip install flake8```

Create a .flake8 file in the root of the project with the following configuration:

[flake8]  
max-line-length = 120  
exclude = migrations, __pycache__, venv, .env

Run Flake8 and generate a report:

```flake8 . --output-file=flake8_report.txt```

Review the report, fix the errors found, and run the command again to verify the corrections.

Note: Errors found in settings.py were intentionally ignored, as this file is automatically generated by Django and is not part of the code written by the development team.
