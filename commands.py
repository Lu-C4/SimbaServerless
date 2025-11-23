
from _commands.check_player_stats import CheckPlayerStats 
from _commands.get_clan_ranking import GetClanRanking
from _commands.get_clan_rank import GetClanRank
from _commands.check_survival_scores import CheckSurvivalScores
from _commands.peek_skins import PeekSkins
from _commands.get_crosshair import GetCrosshair
from _commands.deploy import Deploy
from _commands.clan_player_status import ClanPlayersStatus
from _commands.lobby_links import LobbyLinks
from _commands.super_deploy import SuperDeploy
from _commands.verify import Verify
from _commands.collect_bounty import CollectBounty
from _commands.credits import Credits
from _commands.send_credits import SendCredits


commands = [CheckPlayerStats(),CheckSurvivalScores(),GetCrosshair(),PeekSkins(),GetClanRanking(),GetClanRank(),ClanPlayersStatus(),LobbyLinks(),Verify(),CollectBounty(),Credits(),SendCredits()]
commands.extend([SuperDeploy(),Deploy()])
