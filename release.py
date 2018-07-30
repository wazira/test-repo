import re
import git
import subprocess
import lxml.etree as ET

XML_NAMESPACE_RE = r'{.*}'
RELEASE_TAG_RE = r'-rc[0-9]+\b'
RELEASE_BRANCH_RE = r'release-nvc-[0-9]+.[0-9]+(.[0-9]+)?\b'

RELEASE_TAG_MESSAGE = r'Release %s of project NVC'


def get_xml_namespace(tag):
    match_obj = re.match(XML_NAMESPACE_RE, tag)
    return match_obj.group(0) if match_obj else ''


def prepend_xml_namespace(namespace, tag):
    return (namespace + tag) if namespace else tag


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
        print 'Not a Git repository'
        print 'Run this script from the base directory of a Git repository'
        return

    current_head = repo.head.ref
    current_branch_name = str(current_head)

    if not is_release_branch(current_branch_name):
        print 'Not a release branch'
        print 'Branch name should be in the format - release-nvc-<version_number>'
        print 'Examples - [release-nvc-2.0, release-nvc-2.0.1]'
        return

    if repo.is_dirty():
        print 'The current branch contains uncommitted changes'
        return

    if not hasattr(repo.remotes, 'origin'):
        print 'No remote with the name - "origin"'
        return

    remote_origin_url = repo.remotes.origin.url

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
    new_git_tag_name = current_branch_name + '-rc' + str(next_rc_count)
    new_git_tag_message = RELEASE_TAG_MESSAGE % new_git_tag_name.strip('release-nvc')

    try:
        xml_tree = ET.parse('pom.xml')
    except:
        print 'Error while parsing pom.xml'
        return

    xml_root = xml_tree.getroot()
    xml_namespace = get_xml_namespace(xml_root.tag)
    full_xml_tag = prepend_xml_namespace(xml_namespace, 'version')
    xml_version = xml_root.find(full_xml_tag)
    if xml_version is None:
        print 'Error - Could not able to find tag "version" inside pom.xml'
        return
    else:
        xml_version_old_text = xml_version.text
        xml_version.text = new_git_tag_name.strip('release-nvc')

    print 'Version in the pom.xml file will be changed from "%s" to "%s"' % (xml_version_old_text, xml_version.text)
    print 'A new annotated git tag "%s" with message "%s" will be created' % (new_git_tag_name, new_git_tag_message)
    print 'Changes will be pushed to the "origin" remote with url - %s' % remote_origin_url
    confirm = raw_input('Please confirm [Y/N]: ')
    if confirm.lower() == 'y':
        print '\nWriting pom.xml..'
        xml_tree.write('pom.xml', encoding="utf-8", xml_declaration=True)

        print 'Committing the changes..'
        repo.index.add(['pom.xml'])
        commit_message = 'Changed version from %s to %s in pom.xml' % (xml_version_old_text, xml_version.text)
        repo.index.commit('-m', commit_message)

        print 'Creating annotated tag..'
        repo.create_tag(new_git_tag_name, message=new_git_tag_message)

        print 'Pushing the changes..'
        # GitPython library does not handle username/password authentication
        # using subprocess.call
        subprocess.call(['git', 'push', 'origin'])
        # Git tags need to be pushed separately
        subprocess.call(['git', 'push', 'origin', new_git_tag_name])
    else:
        print 'Aborting...'
        return


if __name__ == '__main__':
    main()
