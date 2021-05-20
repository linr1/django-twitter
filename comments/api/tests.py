from testing.testcases import TestCase
from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient

COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.linghu = self.create_user('linghu')
        self.linghu_client = APIClient()
        self.linghu_client.force_authenticate(self.linghu)

        self.dongxie = self.create_user('dongxie')
        self.dongxie_client = APIClient()
        self.dongxie_client.force_authenticate(self.dongxie)

        self.tweet = self.create_tweet(self.linghu)

    def test_create(self):
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)
        # won't work without parameters
        response = self.linghu_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # not allow if only has tweet_id
        response = self.linghu_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        response = self.linghu_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        response = self.linghu_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1'*141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        response = self.linghu_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.linghu.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')

    def test_update(self):
        comment = self.create_comment(self.linghu, self.tweet, 'original')
        another_tweet = self.create_tweet(self.dongxie)
        url = '{}{}/'.format(COMMENT_URL, comment.id)

        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)

        response = self.dongxie_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.linghu_client.put(url, {
            'content': 'new',
            'user_id': self.dongxie.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.linghu)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # has to have tweet_id
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # ok with tweet_id, no comments at the beginning
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # comments ordered by time
        self.create_comment(self.linghu, self.tweet, '1')
        self.create_comment(self.dongxie, self.tweet, '2')
        self.create_comment(self.dongxie, self.create_tweet(self.dongxie), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # use both tweet_id and user_id but only tweet_id works in the filter
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.linghu.id,
        })
        self.assertEqual(len(response.data['comments']), 2)