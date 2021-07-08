from inbox.services import NotificationService
from notifications.models import Notification
from testing.testcases import TestCase

class NotificationServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.linghu = self.create_user('linghu')
        self.dongxie = self.create_user('dongxie')
        self.linghu_tweet = self.create_tweet(self.linghu)

    def test_send_comment_notification(self):
        comment = self.create_comment(self.linghu, self.linghu_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        comment = self.create_comment(self.dongxie, self.linghu_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        like = self.create_like(self.linghu, self.linghu_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        like = self.create_like(self.dongxie, self.linghu_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)