# Helper script for setting up your apps local instance
# Contributors:
# Roy Keyes <keyes.roy@gmail.com>

help:
	@echo "Available tasks :"
	@echo "\tgettroop - Output data to file for a specific troop requires (TROOP=X)"
	@echo "\tgetcounty - Output data to file for a specific county requires (COUNTY=X)"

gettroop:
	@python extract_traffic.py -d $$TROOP -t troop -o json

getcounty:
	@python extract_traffic.py -d $$COUNTY -t county -o json
