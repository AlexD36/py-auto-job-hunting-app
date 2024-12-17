
# JobSprint

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.12.3-2A9D8F?style=flat)
![Requests](https://img.shields.io/badge/Requests-2.31.0-264653?style=flat)
![LXML](https://img.shields.io/badge/LXML-5.1.0-8AB17D?style=flat)
![Telegram Bot](https://img.shields.io/badge/Telegram%20Bot-13.7-0088CC?style=flat&logo=telegram&logoColor=white)

**JobSprint** is a smart and simple way to stay updated with the latest job opportunities. It scrapes job boards to find new job listings based on your preferences, then sends you real-time notifications via **Telegram** or **Email** whenever a matching job is posted.

This app is designed to help job seekers stay on top of the job market without needing to constantly check multiple websites. With easy setup and customizable alerts, **JobSprint** is the perfect assistant for anyone looking to land their next job!

![JobSprint](https://github.com/user-attachments/assets/d5b6d236-540b-49e1-8276-1d5216bd2a18)

## Features
- Scrapes job listings from popular job boards.
- Sends real-time notifications via Telegram or Email.
- Customizable job filters: location, job title, etc.
- Easy setup and cloud deployment on **Heroku** or **AWS EC2**.

## Table of Contents
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Deployment](#deployment)
- [Features & Roadmap](#features--roadmap)
- [Contributing](#contributing)
  
---

## Technologies Used

- **Python 3.x**: The main programming language.
- **BeautifulSoup**: For web scraping job listings.
- **Requests**: For HTTP requests to scrape job boards.
- **Telegram API**: For sending real-time job notifications via Telegram.
- **SMTP (Email)**: For sending email notifications (optional).
- **Heroku/AWS EC2**: For deployment and running the app continuously.
- **SQLite (Optional)**: For storing job listings temporarily.
- **Cron Jobs/Heroku Scheduler**: For scheduling job scraping at regular intervals.

---

## Installation

Follow these instructions to set up the app on your local machine or deploy it to the cloud.

### Prerequisites

Make sure you have the following installed:
- Python 3.x
- pip (Python package installer)
- Git (for version control)

### Steps

1. **Clone the Repository**:
   First, clone this repository to your local machine:
   ```bash
   git clone https://github.com/AlexD36/job-hunting-app.git
   cd job-hunting-app
   ```

2. **Install Dependencies**:
   Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Settings**:
   - **Telegram**: Create a bot on Telegram and get your **API token**.
   - **Email (Optional)**: Set up your email SMTP credentials (e.g., Gmail).
   - **Job Filters**: Edit the `config.py` file to set your job filters (location, job title, etc.).

4. **Run the App Locally**:
   To start the app and test locally, run the following command:
   ```bash
   python main.py
   ```

5. **Start Receiving Alerts**:
   Once the app is running, it will scrape the job boards and send notifications based on your preferences.

---

## Usage

The **JobSprint** app scrapes job boards and sends notifications based on the configured filters. Here’s how it works:

1. **Scraping**:
   - The app scrapes job boards (e.g., LinkedIn, Indeed) for listings that match your criteria.
   - You can filter by job title, location, and other key details.

2. **Notification**:
   - When a matching job is found, you’ll receive a notification on your chosen platform (Telegram or Email).
   - You can customize how frequently you’d like to receive updates (instant, daily, weekly).

---

## Deployment

You can deploy this app to cloud services like **Heroku** or **AWS EC2** for continuous running.

### Deploy on Heroku (Recommended)

1. **Create a Heroku Account**: Sign up on [Heroku](https://www.heroku.com).
2. **Install Heroku CLI**: Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
3. **Deploy the App**:
   - In the root directory of your app, initialize a git repository if you haven’t already:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     ```
   - Log into Heroku:
     ```bash
     heroku login
     ```
   - Create a Heroku app:
     ```bash
     heroku create
     ```
   - Push your code to Heroku:
     ```bash
     git push heroku master
     ```
   - Set up periodic job scraping using Heroku Scheduler.

### Deploy on AWS EC2 (Alternative)

1. **Launch an EC2 Instance**: Use the [AWS EC2 Dashboard](https://aws.amazon.com/ec2/) to create an Ubuntu server.
2. **Set Up the Environment**: SSH into your EC2 instance, install Python and necessary dependencies.
3. **Run the Script**: Set up a cron job to run the app periodically.

---

## Contributing

Contributions are welcome! Here’s how you can contribute to the development of the app:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -am 'Add feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a pull request with a detailed description of the changes.

---

## Acknowledgements

- **BeautifulSoup**: For web scraping.
- **Telegram API**: For sending real-time notifications.
- **Heroku/AWS**: For cloud deployment.
- **Job boards**: For providing job listings.

---
