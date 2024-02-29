# Get Postman Collection

Fetch a postman collection based on the collection name and a fork (if provided).

The intent is to get the version of the collection that matches the branch name, so that the right postman tests are run.

For example, if your branch is `123-do-the-thing` and your postman collection was forked with the same name, you would use the following:

```yml
- name: Get Postman Collection
  uses: TheKeyholdingCompany/action-get-postman-collection@v0.0.1
  with:
    postman-key: your-key-here
    collection-name: Awesome API Collection
    collection-fork: 123-do-the-thing
```

If the fork doesn't exist in postman, then the action will default to the main collection.
