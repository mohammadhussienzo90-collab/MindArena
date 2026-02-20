import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FriendRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
                    default='pending',
                    max_length=20,
                )),
                ('message', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('from_player', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sent_friend_requests',
                    to='accounts.player',
                )),
                ('to_player', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='received_friend_requests',
                    to='accounts.player',
                )),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('from_player', 'to_player')},
            },
        ),
        migrations.CreateModel(
            name='Friendship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player1', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='friendships_as_player1',
                    to='accounts.player',
                )),
                ('player2', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='friendships_as_player2',
                    to='accounts.player',
                )),
            ],
            options={
                'unique_together': {('player1', 'player2')},
            },
        ),
    ]
