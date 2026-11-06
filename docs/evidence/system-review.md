# Project Final Review and Reflection

## Addressing Relevant Implications

### Privacy

The only personal information I collect from users is a first name, last name, username and password. Passwords are never stored in plain text: they are turned into a hash with generate_password_hash when someone signs up, and login uses check_password_hash to compare. All text typed into forms is escaped with html.escape before it is saved, and every SQL query uses ? placeholders so user input can't be used to attack the database. Uploaded image names are made safe with secure_filename. Every page that shows family data uses @login_required, and the data is filtered by the family stored in the session, so someone outside a family can't see its stories or people. A family can only be joined with its 6-character code, and only the owner can see that code on the family page.

### Legal

The app only stores information that is relevant to the family (names, dates, stories and photos), and I don't collect anything extra about users. User details are kept in a database with the passwords hashed, as planned. Photos and stories are added by the family members themselves, so copyright is not a problem, and the app is only shared within each family through the join code. People can edit or delete the stories and people they added, which gives them control over their own information. 

### Functionality

The app does what the requirements asked: users can post stories and add people with photos, and can edit and delete the things they added. The data is stored in a database of six linked tables (users, families, members, people, stories and involves) rather than in a list, and images are uploaded to a folder with only the filename stored in the database. Each page loads only the data it needs for the chosen family. Testing found a lot of errors that I fixed, such as stories showing in the wrong family, tags not saving and members not listing.

### Aesthetics

I used one colour palette throughout the site, set once as CSS variables (dark blue, orange accent and a cream paper colour) so every page matches. Buttons, forms, story cards and people cards all use the same styling, and the same header and navigation appear on every page.

### Usability

The navigation is in the same place on every page, and every action shows a clear flash message, with errors and successes styled differently (for example "Story added" or "You can only edit your own stories"). Edit forms have a Cancel button so users don't get stuck, and a person can't be added without at least one name, with the error explaining what to enter. On the story form, the people picker is a dropdown of checkboxes instead of a multi-select box, because holding Ctrl to pick several people doesn't work on a phone. Cards link to the single story and person pages, and the pages for a family show only that family's information so users aren't overwhelmed.

## Overall Review

**What went well** - The core of the app works: users can sign up, create or join a family, and then add, view, edit and delete stories and people with photos, all stored properly in a linked database. Filtering everything by the family stored in the session kept each family's data separate. Sticking to the techniques from my course notes made the code consistent across all the routes.

**What didn't go so well** - I lost time to errors from redirects and links pointing at pages that didn't exist, and from queries with the wrong number of parameters. Every time I changed the database structure I had to reset the database and lose my test data. Docker, running in a OneDrive folder, caused a "disk I/O error" that stopped the app from starting for a while. 

**How did the testing/trialling impact the final system** - Testing with more than one account and more than one family found the biggest problems: stories showing in the wrong family, people who weren't in a story's family being taggable, and the join code showing to every member. Fixing these led to the family_id column on stories, the family-filtered queries, the owner-only join code and the checkbox people picker.

**What would I do differently** - I would plan the database fully before building, including family ids and who added each record, so I didn't have to keep resetting it. I would also keep my project outside OneDrive from the start, test on a phone earlier, and name my routes consistently from the beginning.