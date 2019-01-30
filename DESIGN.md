# Technisch ontwerp
## Controllers

Functienaam | Beschrijving | Get of Post?
------------|--------------|-------------
Register | Hier kan de gebruiker een account aanmaken. Deze pagina is zowel een get als een post. | Beide
Login | Hier kan de gebruiker met een aangemaakt account inloggen. Deze pagina is zowel een get als een post. | Beide
Index | De homepage met informatie en links naar andere pagina’s. Ook staan de actieve games waar de gebruiker in zit hier. Deze kan de gebruiker meteen spelen, dus er is zowel een get als post nodig. Ook is er een pagina voor nodig. | Beide
Logout | Deze functie logt de user uit. Er is geen pagina voor nodig en ook geen requests, aangezien het een redirect is naar login. | n.v.t.
Find_game | Hier kan de gebruiker andere gebruikers opzoeken om uit te dagen. Zowel een get als een post. Er is een pagina voor nodig. | Beide
Browse_users | Hier kan de gebruiker andere gebruikers zien op basis van de ingetypte naam in find_game. De gebruiker kan hier mensen uitdagen. Er is een get en een post voor nodig. Ook is er een pagina nodig. | Beide
Play | Hier kan de gebruiker vragen beantwoorden. Het controleren van het antwoord gebeurt in de functie. Zodra de gebruiker een fout maakt, wordt zijn/haar score opgeslagen/bepaald wie er gewonnen heeft. Hier is een pagina voor nodig. | Beide
History | Laat de 10 meest recente games zien waar de gebruiker aan heeft meegedaan, inclusief score. Hier is alleen een get nodig. Ook is er een pagina vereist. | Get
Leaderboard | Hier zijn de 8 spelers (en hun aantal wins) met de meeste gewonnen games te zien. Er is alleen een een get nodig. Ook is er een pagina nodig. | Get
Forgottenpassword | Hiermee kan de gebruiker een nieuw random wachtwoord ontvangen via de mail, hiervoor is wel een emailadres nodig. Alleen een get, omdat het e-mailadres al in de database staat. | Get
Instaplay | Deze methode selecteert een willekeurige gebruiker om een potje mee te starten als de tegenstander voor de speler niet uit maakt. | Get
Profile | Hier kan de gebruiker zijn wachtwoord veranderen. Hiervoor dient de gebruiker zijn huidige wachtwoord en tweemaal zijn nieuwe wachtwoord als input te geven. Ook zorgt deze functie ervoor dat de gebruiker kan zien hoeveel games hij of zij gewonnen heeft.| Beide

## Views 
Hierbij de route door de website: 
https://drive.google.com/open?id=1S7gX163vIsATuphYjzWSVpuXKphZAffQ

## Models en helpers

Naam(parameters) | Beschrijving
-----------------|-------------
Login_required | Deze decorator checkt of de gebruiker is ingelogd.
Create_game(player1_id, player2_id) | Deze functie accepteert 2 ID’s en maakt vervolgens een database entry voor de nieuwe game.
Find_username(user_id) | Deze functie geeft de gebruikersnaam van een user terug op basis van de ID van de user.
Finish_game(result, game_id) | Deze functie slaat de uitslag van de game op en verwijdert de vragen uit de database (om ruimte te besparen). Deze werden opgeslagen om te zorgen dat de spelers die tegen elkaar spelen dezelfde vragen beantwoorden.
Index_info(user_id) | Deze functie geeft alle games waar de gebruiker in zit terug om deze op de homepagina te tonen.
Init_game(game_id) | Deze functie vraagt de vragen in een dictionary, de spelers en de score van tegenstander van de huidige speler als deze al heeft gespeeld op.
Send_mail(requester_mail, new_password) | Deze functie verstuurt een mail met een nieuw wachtwoord naar de mail van de gebruiker als deze zijn wachtwoord is vergeten.
Update_score(score, game_id, status) | Deze functie slaat de score van de speler op als hij de eerste in het potje is die zijn vragen beantwoord heeft en veranderd de status naar actief.
Search_user(username) | Deze functie geeft de usernames van gebruikers die (deels) overeenkomen met de parameter. Hiervoor wordt een wildcard gebruikt. De wildcard is wat de gebruiker invoert bij het zoeken van de tegenstander.
User_history(user_id) | Deze functie laat de 10 meest recente beëindigde games van de gebruiker met de tegenstander en uitslag zien.
Find_matchup(game_id) | Deze functie geeft de spelers in een potje terug als er een ID van het potje is gegeven.
Find_won(user_id) | Deze functie geeft aan hoe vaak een speler gewonnen heeft.
Increase_won(user_id) | Deze functie telt één bij het aantal gewonnen potjes op als de speler heeft gewonnen.
Highest() | Deze functie toont de gebruikersnamen en het aantal gewonnen potjes van de acht spelers die het vaakst hebben gewonnen.
Has_access(game_id, user_id) | Deze functie checkt of de gebruiker toestemming heeft om deel te nemen aan een opgegeven game.
Find_rows(username) | Deze functie geeft alle informatie van een speler op basis van hun username (onafhankelijk van hoofdletters).
Create_user(username, hashed, games_won) | Deze functie maakt een nieuwe gebruiker aan en slaat zijn gegevens op.
Check_exists(username) | Deze functie haalt de ID van een speler op. Het doel van deze functie is om te checken of de gebruiker al bestaat. Als deze functie dus leeg terugkomt, betekent het dat de gebruikersnaam nog niet bestaat.
All_ids() | De functie geeft de ID’s van alle spelers terug.
Mail_to_name(mail) | Deze functie geeft de gebruikersnaam dat gekoppeld is aan het gegeven mailadres.
Reset_password(new_password, username) | Deze functie verandert het wachtwoord van de gebruiker die gegeven is als parameter naar het wachtwoord dat als parameter gegeven is.
All_correct(game_id, to_beat, user_id, players) | Deze functie beëindigt het potje als de huidige gebruiker alle vijftig vragen goed heeft.
Create_result(player1, score1, score2, player2) | Deze functie geeft de score op een mooi geformatteerde manier terug. Voorbeeld:”Speler1 5-4 Speler2”
Reset_session(finishCode, correctAnswer) | Deze functie reset de huidige sessie variabelen.
Total_games(user_id) | Deze functie haalt uit de database op hoeveel potjes de speler heeft gespeeld.
Correct_password(password, user_id) | Deze functie checkt of het ingevoerde wachtwoord klopt met het daadwerkelijke wachtwoord van de gebruiker.
Mail_exists(mail) | Deze functie zoekt een mailadres in de database op om te kijken of deze bestaat.

## Plugins en frameworks

### Trivia Database
Wij zullen niet veel hulp nodig hebben van buitenaf. Wel zullen we afhangen van een API waar wij de vragen uit gaan opvragen. De meest geschikte API die wij hiervoor hebben gevonden is te vinden op www.opentdb.com. Wij hebben hiervoor gekozen omdat naast een categorie ook de moeilijkheid van de vraag gekozen kan worden. Daarnaast ligt het maximaal mogelijk aantal requests dusdanig hoog dat wij die bovengrens niet hebben kunnen vinden. Dit is dus gunstig voor onze applicatie als het aantal gebruikers zou stijgen.

### Bootstrap
Daarnaast kunnen wij meerdere componenten van Bootstrap gebruiken om te zorgen dat we niet voor de tweede keer het wiel uit gaan vinden. Componenten die wij uit het framework kunnen halen zijn bijvoorbeeld de badges en de alerts. De documentatie kan gevonden worden op www.getbootstrap.com/docs/4.1/getting-started/introduction/.

### Jquery
We zullen ook gebruik maken van Jquery, om ons het leven makkelijker te maken bij het gebruik van javascript. 
