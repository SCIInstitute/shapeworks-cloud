# Setting up your Shapeworks Cloud instance

1. Clone https://github.com/girder/shapeworks-cloud and open that directory in your code editor. Check out the appropriate branch.

2. In a terminal (in your repo directory), run `docker-compose up`. You may need to install docker. Keep this command running; this is the development server.

3. In a second terminal (also in your repo directory), create an admin user for your server instance. Do so by running `docker exec -it [django] ./manage.py migrate` followed by `docker exec -it [django] ./manage.py createsuperuser`. Replace `[django]` with the name of the django container currently running after step 2. To find the name of the django container, run `docker ps` and look for the entry containing "django". When creating the admin user, remember your credentials. It is easiest if your username equals your email.

4. Open a terminal in this directory. Run `python3 ./upload_examples.py` in this directory to add data to your current server's database. You will work with this example data as you work on the client (Vue) code. Tip: watch the server printout as you run this to see what the script is doing.

5. After running this script, navigate to localhost:8081 in your browser. Log in with your admin credentials from step 3. The dataset that you have added now has all steps (Groom, Optimize, Analyze) complete.
