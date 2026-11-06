# Project Final Review and Reflection

## Addressing Relevant Implications

### Privacy

My requirements said I should only collect the information I need and not store it in an unsafe way. The only personal information the app collects is a first name, last name, username and password. Passwords are never stored in plain text, they are hashed with generate_password_hash when someone signs up, and login compares them with check_password_hash. Uploaded image names are made safe with secure_filename and every page that shows family data uses @login_required, and everything is filtered by the family stored in the session, so people outside a family can't see its stories or people. A family can only be joined with its 6-character code, and only the owner can see that code.

### Legal

I said that copyright wouldn't affect me much because the app only stores records and photos that are relevant to my family, and that storing user data properly would matter most. The app doesn't collect anything extra about users, and their passwords are hashed in the database. Photos and stories are added by the family members themselves, and each family is private and only joined through its code. People can edit or delete the stories and people they added, so they stay in control of their own information.

### Functionality

My requirements said users should be able to post text and photos and edit or delete them, and that the data should be stored properly instead of in a list. The app does this. Stories and people (with optional photos and social media links) can be added, edited and deleted by the person who added them. The data is kept in a database of six linked tables (users, families, members, people, stories and involves), and images are uploaded to a folder with only the filename stored in the database. I tested the app on a computer and a phone, and testing found and fixed a lot of errors, such as stories showing in the wrong family, tags not saving and members not listing.

### Aesthetics

I planned one clean, consistent colour palette. The whole site uses the same colours, set once as CSS variables (dark blue, an orange accent and a cream paper colour), so buttons, forms, story cards and people cards all match, and the same header and navigation are on every page. This keeps the site looking trustworthy instead of "dodgy".

### Usability

I wanted every page to have a way out and clear messages, because older users could get lost. The navigation is the same on every page, and each action shows a clear success or error message (for example "Story added" or "You can only edit your own stories"). The edit forms have a Cancel button, and mistakes like adding a person with no name give an error that explains what to enter. On the story form, the people picker is a collapsible dropdown of checkboxes, which keeps the form short on a phone. Following my stakeholder's feedback, the Edit button now sits in the corner of each story card and Logout is the furthest link to the right.

## UX Principles

- **Know your user:** I tested the layout on a phone as well as a computer, and changed the people picker to a dropdown because the form was too long on mobile.
- **Consistent and clear:** The same layout, navigation and button styles are used on every page, and buttons are in obvious places, such as edit in the corner of each card and leave family centred on the family page.
- **Test and improve:** I gave the app to my stakeholder, who suggested the edit button and the Logout position, and I changed both.

## Overall Review

**What went well** - The core of the app works, users can sign up, create or join a family, and add, view, edit and delete stories and people with photos, all stored properly in a linked database. Filtering everything by the family stored in the session kept each family's data private. 

**What didn't go so well** - I lost time to errors from redirects and links pointing at pages that didn't exist, and from queries with the wrong number of parameters. Every time I changed the database structure I had to reset the database and lose my test data. Docker, running in a OneDrive folder, caused a "disk I/O error" that stopped the app from starting for a while.

**How did the testing/trialling impact the final system** - Testing with more than one account and more than one family found the biggest problems which was stories showing in the wrong family, people from other families being taggable, and the join code being visible to every member. Fixing these led to the family_id column on stories, the family-filtered queries, the owner-only join code and the checkbox people picker. Feedback from my stakeholder changed the Edit button and the position of Logout, and testing on a phone led to the dropdown for tagging people.

**What would I do differently** - I would plan the database fully before building, including family ids and who added each record, so I didn't have to keep resetting it. 