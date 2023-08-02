**Like Requirements**

1. Allow a user to like a message. Users cannot like their own messages.
2. Allow a user to unlike a message.
3. Allow a user to view a count of their liked messages on their profile page.
4. Allow a user to view a filtered list of messages that shows only their liked messages.
5. Message like status should be a star that is filled in / empty to show like status.
6. Clicking on a star should change like status.

**Work Items**

1. Add a Like model. **DONE**
2. Add stars to message cards.
-- /messages/show.html
-- /users/show.html
-- /home.html
3. Update 'Likes' count on profile page.
4. Create a profile view where only liked messages show.
5. Add POST view function for liking / un-liking a star.
6. Add a GET view function for displaying starred messages on profile.