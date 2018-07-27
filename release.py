import git
import re

RELEASE_BRANCH_RE = r'release-nvc-[0-9]+.[0-9]+(.[0-9]+)?\b'
RELEASE_TAG_RE = r'-rc[0-9]+\b'

RELEASE_TAG_MESSAGE = 'Release %s of project NVC'


def match_re(pattern, string):
    match_obj = re.match(pattern, string)
    if match_obj is not None:
        return True
    else:
        return False


def is_release_branch(branch_name):
    return match_re(RELEASE_BRANCH_RE, branch_name)


def is_release_branch_tag(branch_name, tag_name):
    release_branch_tag_re = branch_name + RELEASE_TAG_RE
    return match_re(release_branch_tag_re, tag_name)


def main():
    try:
        repo = git.Repo('.')
    except git.InvalidGitRepositoryError:
        print 'Not a Git repository.'
        print 'Run this script from the base directory of a Git repository'
        return

    current_head = repo.head.ref
    current_branch_name = str(current_head)

    if not is_release_branch(current_branch_name):
        print 'Not a release branch.'
        print 'Branch name should be in the format - release-nvc-<version_number>'
        print 'Examples - [release-nvc-2.0, release-nvc-2.0.1]'
        return

    if repo.is_dirty():
        print 'The current branch contains uncommitted changes.'
        return

    rc_count_list = list()
    rc_count = 0
    rc_count_last = 0

    for tag in repo.tags:
        tag_name = str(tag)
        if is_release_branch_tag(current_branch_name, tag_name):
            rc_count = int(tag_name.split('rc')[1])
            rc_count_list.append(rc_count)

    if len(rc_count_list) > 0:
        rc_count_list.sort()
        rc_count_last = rc_count_list.pop()

    next_rc_count = rc_count_last + 1
    new_tag_name = current_branch_name + '-rc' + str(next_rc_count)
    new_tag_message = RELEASE_TAG_MESSAGE % new_tag_name.strip('release-nvc')

    print 'Creating new annotated tag "%s" with message "%s"' % (new_tag_name, new_tag_message)
    confirm = raw_input('Please confirm [Y/N]: ')
    if confirm.lower() == 'y':
        repo.create_tag(new_tag_name, message=new_tag_message)
    else:
        print 'Aborting...'


if __name__ == '__main__':
    main()