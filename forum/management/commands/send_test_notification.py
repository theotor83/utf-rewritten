"""
Django management command to send test notifications to all users
Usage: python manage.py send_test_notification
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import json
from forum.signals import redis_client


class Command(BaseCommand):
    help = 'Send a test notification to all users via Redis pub/sub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send notification to a specific user ID only',
        )
        parser.add_argument(
            '--message',
            type=str,
            default='Test de notification Redis - Ceci est un message de test!',
            help='Custom message to send',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("📡 SENDING TEST NOTIFICATIONS"))
        self.stdout.write("=" * 70)
        
        # Check if Redis client is available
        if redis_client is None:
            self.stdout.write(self.style.ERROR("\n❌ Redis client is not available!"))
            self.stdout.write(self.style.ERROR("   Please check Redis connection."))
            return
        
        # Test Redis connection
        try:
            redis_client.ping()
            self.stdout.write(self.style.SUCCESS("\n✅ Redis connection: OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Redis connection failed: {e}"))
            return
        
        # Get users to notify
        if options['user_id']:
            users = User.objects.filter(id=options['user_id'])
            if not users.exists():
                self.stdout.write(self.style.ERROR(f"\n❌ User with ID {options['user_id']} not found"))
                return
        else:
            users = User.objects.all()
        
        user_count = users.count()
        self.stdout.write(f"\n📊 Target users: {user_count}")
        self.stdout.write(f"📝 Message: {options['message']}\n")
        
        # Send notifications
        success_count = 0
        fail_count = 0
        
        for user in users:
            channel_name = f"user_notifications_{user.id}"
            
            notification = {
                'message': options['message'],
                'text_preview': 'Si vous voyez ce message, Redis fonctionne correctement!',
                'post_url': '#',
                'author_username': 'System',
                'topic_full_title': 'Test de notification Redis',
            }
            
            try:
                subscribers = redis_client.publish(channel_name, json.dumps(notification))
                success_count += 1
                
                if subscribers > 0:
                    self.stdout.write(
                        f"   ✅ User {user.username} (ID: {user.id}) - "
                        f"{subscribers} subscriber(s) listening"
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"   ⚠️  User {user.username} (ID: {user.id}) - "
                            f"No active subscribers"
                        )
                    )
            except Exception as e:
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"   ❌ User {user.username} (ID: {user.id}) - Failed: {e}"
                    )
                )
        
        # Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"📈 SUMMARY"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"   Total users: {user_count}")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Successful: {success_count}"))
        if fail_count > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ Failed: {fail_count}"))
        
        self.stdout.write("\n💡 Tips:")
        self.stdout.write("   - If 'No active subscribers', users need to be logged in and listening")
        self.stdout.write("   - Check your frontend WebSocket/SSE implementation")
        self.stdout.write("   - Notifications are published but not stored (real-time only)")
        self.stdout.write("")
