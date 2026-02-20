"""Notification service layer — centralized notification creation."""
from .models import Notification


class NotificationService:
    """Stateless service class for creating notifications."""

    @staticmethod
    def send(recipient, notification_type, title_en, title_ar='',
             message_en='', message_ar='', data=None):
        """Create and return a Notification.

        Args:
            recipient: Player instance who receives the notification.
            notification_type: One of the NOTIFICATION_TYPE_CHOICES values.
            title_en: English title.
            title_ar: Arabic title (optional).
            message_en: English message body (optional).
            message_ar: Arabic message body (optional).
            data: Extra JSON payload (optional).

        Returns:
            The newly created Notification instance.
        """
        return Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar=message_ar,
            data=data or {},
        )

    @staticmethod
    def send_achievement(player, achievement):
        """Create a notification for earning an achievement.

        Args:
            player: Player who earned the achievement.
            achievement: Achievement instance that was earned.

        Returns:
            Notification instance.
        """
        return NotificationService.send(
            recipient=player,
            notification_type='achievement',
            title_en=f'Achievement Unlocked: {achievement.title_en}',
            title_ar=f'\u0625\u0646\u062c\u0627\u0632 \u062c\u062f\u064a\u062f: {achievement.title_ar}' if achievement.title_ar else '',
            message_en=achievement.description_en,
            message_ar=achievement.description_ar,
            data={
                'achievement_id': achievement.id,
                'achievement_slug': achievement.slug,
                'xp_reward': achievement.xp_reward,
            },
        )

    @staticmethod
    def send_arena_invite(player, match):
        """Create a notification for an arena match invitation.

        Args:
            player: Player being invited.
            match: ArenaMatch instance.

        Returns:
            Notification instance.
        """
        return NotificationService.send(
            recipient=player,
            notification_type='arena_invite',
            title_en=f'Arena Invite: {match.get_match_type_display()} Match',
            title_ar='\u062f\u0639\u0648\u0629 \u0644\u0644\u0633\u0627\u062d\u0629',
            message_en=f'You have been invited to a {match.get_match_type_display()} match!',
            message_ar='\u0644\u0642\u062f \u062a\u0645\u062a \u062f\u0639\u0648\u062a\u0643 \u0625\u0644\u0649 \u0645\u0628\u0627\u0631\u0627\u0629!',
            data={
                'match_id': match.id,
                'match_type': match.match_type,
            },
        )

    @staticmethod
    def send_arena_result(player, match, won):
        """Create a notification for an arena match result.

        Args:
            player: Player who participated.
            match: ArenaMatch instance (must be completed).
            won: Boolean indicating whether the player won.

        Returns:
            Notification instance.
        """
        if won:
            title_en = 'Victory! You won the arena match!'
            title_ar = '\u0641\u0648\u0632! \u0644\u0642\u062f \u0631\u0628\u062d\u062a \u0627\u0644\u0645\u0628\u0627\u0631\u0627\u0629!'
            message_en = f'Congratulations! You won the {match.get_match_type_display()} match with an ELO change of +{match.elo_change}.'
        else:
            title_en = 'Arena match completed'
            title_ar = '\u0627\u0646\u062a\u0647\u062a \u0627\u0644\u0645\u0628\u0627\u0631\u0627\u0629'
            message_en = f'The {match.get_match_type_display()} match has ended. Better luck next time!'

        return NotificationService.send(
            recipient=player,
            notification_type='arena_result',
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar='',
            data={
                'match_id': match.id,
                'match_type': match.match_type,
                'won': won,
                'elo_change': match.elo_change,
            },
        )

    @staticmethod
    def send_friend_request(player, from_player):
        """Create a notification for an incoming friend request.

        Args:
            player: Player receiving the friend request.
            from_player: Player who sent the request.

        Returns:
            Notification instance.
        """
        return NotificationService.send(
            recipient=player,
            notification_type='friend_request',
            title_en=f'{from_player.display_name} sent you a friend request',
            title_ar=f'{from_player.display_name} \u0623\u0631\u0633\u0644 \u0644\u0643 \u0637\u0644\u0628 \u0635\u062f\u0627\u0642\u0629',
            message_en='Accept the request to start competing together!',
            message_ar='\u0627\u0642\u0628\u0644 \u0627\u0644\u0637\u0644\u0628 \u0644\u0628\u062f\u0621 \u0627\u0644\u0645\u0646\u0627\u0641\u0633\u0629 \u0645\u0639\u064b\u0627!',
            data={
                'from_player_id': from_player.id,
                'from_player_name': from_player.display_name,
            },
        )

    @staticmethod
    def send_level_up(player, new_level):
        """Create a notification for levelling up.

        Args:
            player: Player who levelled up.
            new_level: The new overall level.

        Returns:
            Notification instance.
        """
        return NotificationService.send(
            recipient=player,
            notification_type='level_up',
            title_en=f'Level Up! You reached level {new_level}',
            title_ar=f'\u0645\u0633\u062a\u0648\u0649 \u062c\u062f\u064a\u062f! \u0648\u0635\u0644\u062a \u0625\u0644\u0649 \u0627\u0644\u0645\u0633\u062a\u0648\u0649 {new_level}',
            message_en=f'Congratulations! You are now level {new_level}. Keep up the great work!',
            message_ar=f'\u062a\u0647\u0627\u0646\u064a\u0646\u0627! \u0623\u0646\u062a \u0627\u0644\u0622\u0646 \u0641\u064a \u0627\u0644\u0645\u0633\u062a\u0648\u0649 {new_level}.',
            data={
                'new_level': new_level,
            },
        )
