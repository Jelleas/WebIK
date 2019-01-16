Technisch ontwerp

Controllers

Functienaam         Beschrijving                                                            Get of Post?
Register            Hier kan de gebruiker een account aanmaken.                             Beide
Login               Hier kan de gebruiker met een aangemaakt account inloggen.              Beide
Index               De homepage met informatie en links naar andere pagina’s. Ook kan de    Get
                    gebruiker uitslagen van reeds gespeelde games bekijken 
start_game          Hier kan de gebruiker andere gebruikers opzoeken, of een willekeurige   Beide
                    gebruiker vinden om uit te dagen.
In_game             Hier kan de gebruiker vragen beantwoorden. Het controleren van het      Beide
                    antwoord gebeurt in de functie.
current_games       Laat alle games waar de gebruiker aan meedoet zien. De post zorgt       Beide
                    ervoor dat de gebruiker in-game komt in de game die geselecteerd is.
change_password     Hier kan de gebruiker zijn wachtwoord veranderen. Hiervoor is wel een   Get
                    e-mailadres nodig. Deze pagina is alleen een get, omdat het e-mailadres 
                    al in de database staat. 
                    
Views
Hierbij de route door de website: https://drive.google.com/open?id=1S7gX163vIsATuphYjzWSVpuXKphZAffQ
Models en helpers
Format_question: deze helper haalt de vragen uit de database en zet ze om in een duidelijke vorm.

Create_game: deze functie accepteert 2 ID’s en maakt vervolgens een database entry voor de nieuwe game.

Stalemate: deze functie wordt aangeroepen als de scores van de spelers gelijk zijn. Deze maakt steeds een moeilijke vraag aan, tot een van de spelers er één meer goed heeft dan de tegenstander. Dit systeem is vergelijkbaar met het systeem van de penalty shoot-outs uit het voetbal en hockey.

Login_required: deze functie checkt of de gebruiker is ingelogd.

Plugins en frameworks
Trivia Database
Wij zullen niet veel hulp nodig hebben van buitenaf. Wel zullen we afhangen van een API waar wij de vragen uit gaan opvragen. De meest geschikte API die wij hiervoor hebben gevonden is te vinden op www.opentdb.com. Wij hebben hiervoor gekozen omdat naast een categorie ook de moeilijkheid van de vraag gekozen kan worden. Daarnaast ligt het maximaal mogelijk aantal requests dusdanig hoog dat wij die bovengrens niet hebben kunnen vinden. Dit is dus gunstig voor onze applicatie als het aantal gebruikers zou stijgen.
Bootstrap
Daarnaast kunnen wij meerdere componenten van Bootstrap gebruiken om te zorgen dat we niet voor de tweede keer het wiel uit gaan vinden. Componenten die wij uit het framework kunnen halen zijn bijvoorbeeld de badges en de alerts. De documentatie kan gevonden worden op www.getbootstrap.com/docs/4.1/getting-started/introduction/.
