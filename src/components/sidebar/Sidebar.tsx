import i18n from '@dhis2/d2-i18n'
import { IconChevronLeft24 } from '@dhis2/ui'
import cx from 'classnames'
import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'
import { Sidenav, SidenavItems, SidenavLink } from './sidenav'

type LinkItem = { to: string; label: string }

const SidebarNavLink = ({ to, label, end }: LinkItem & { end?: boolean }) => (
    <SidenavLink to={to} label={label} end={end} LinkComponent={NavLink} />
)

export const Sidebar = ({ className }: { className?: string }) => {
    const [collapsed, setCollapsed] = useState(false)

    return (
        <aside
            className={cx(styles.asideWrapper, className, {
                [styles.collapsed]: collapsed,
            })}
        >
            <Sidenav>
                <SidenavItems>
                    <SidebarNavLink
                        to="/"
                        label={i18n.t('Create new role')}
                        end
                    />
                    <SidebarNavLink
                        to="/update"
                        label={i18n.t('Update existing role')}
                    />
                </SidenavItems>
            </Sidenav>
            <button
                className={styles.collapseButton}
                type="button"
                onClick={() => setCollapsed(!collapsed)}
            >
                <div
                    className={cx(styles.iconWrapper, {
                        [styles.collapsed]: collapsed,
                    })}
                >
                    <IconChevronLeft24 />
                </div>
            </button>
        </aside>
    )
}
