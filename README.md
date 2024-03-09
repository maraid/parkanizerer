
[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)

# Parkanizerer

_A tool that books an office desk on [tidaro.com](https://www.tidaro.com) ([parkanizer.com](https://share.parkanizer.com/) before)._ 

## Commands
Check the help page with `parkanizerer.py -h` for parameters
### `book-desk`
With this mode you can book desks in advance automatically.
  - One way you can achive that is by typing weekdays in `config.toml` file. When the script runs it'll check for those days if they are available in tidaro and books them. 
  - The other way is that you either leave the weekdays field empty or remove it completely. This way when the script runs, it'll book a desk for you in advance for for the current day. This way you can utilize crontab to run it for you.

Note that it is greedy, meaning it'll book all days that are available. So if you specify monday, it'll book all mondays that are available in tidaro.

*Don't forget to release your desk if you decide not to go to the office.*

### `generate-map`
With this mode you can generate a map of reservations of your collegues. It works by requesting all the employee reservations one by one so it takes a couple of minutes to get all the bookings.

It's only useful if the organization doesn't allow you this by default.

## Installation and Usage
1. Make sure you have minimum [python 3.12.x](https://www.python.org/downloads/). Check with `python --version`
2. Clone this repo
```bash
git clone git@github.com:maraid/parkanizerer.git
```
3. Either setup a virtualenv or use the global one.
```bash
cd parkanizerer
# create a virtualenv and activate it-
python -m pip install -r requirements.txt
```

4. Setup your configuration by creating `config.toml` based on [`config.example.toml`](https://github.com/maraid/parkanizerer/blob/master/config.example.toml). Log in to parkanizer and check the exact name of the zone and desk that you want to book.


### `book-desk` usage
#### Linux
If you want to use automatic bookings with crontab add entries with  `crontab -e`

```text
  1 0 * * 1 /path/to/parkanizerer/venv/Sripts/python.exe /path/to/parkanizerer/parkanizerer.py &>> /path/to/parkanizerer/parkanizerer.log
```
This will run the script on each monday one minute after midnight and it'll book the selected desk for the next week.

#### Windows

Create a batch file under the name of `parkanizerer.cmd`. Add this line to it and edit the paths to represent your setup.
```batch
/path/to/parkanizerer/venv/Sripts/activate
/path/to/parkanizerer/parkanizerer.py
```
Create a shortcut of the newly created file and copy it to the windows Startup folder. You can find this easily by pressing `Win+R` and typing `shell:startup`.

## License

[MIT](https://choosealicense.com/licenses/mit/)
