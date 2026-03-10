import instaloader

SOURCE_USERNAME = "bittu_all_remix"

def test_fetch():
    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L, SOURCE_USERNAME)
        
        reels = []
        for post in profile.get_posts():
            if post.is_video:
                reels.append({
                    'id': str(post.postid),
                    'url': post.url,
                    'caption': post.caption if post.caption else ""
                })
        
        print(f"Found {len(reels)} reels")
        for reel in reels[:3]:
            print(f"ID: {reel['id']}, URL: {reel['url']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()
