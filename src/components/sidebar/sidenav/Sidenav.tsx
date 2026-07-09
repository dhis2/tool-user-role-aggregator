import { IconChevronDown16 } from '@dhis2/ui'
import cx from 'classnames'
import React, { PropsWithChildren } from 'react'
import styles from './Sidenav.module.css'

export const Sidenav = ({
    children,
    className,
}: PropsWithChildren<{ className?: string }>) => (
    <nav className={cx(styles.sidenavWrap, className)}>{children}</nav>
)

export const SidenavItems = ({ children }: PropsWithChildren) => (
    <ul className={styles.sidenavItems}>{children}</ul>
)

export const SidenavFooter = ({ children }: PropsWithChildren) => (
    <div className={styles.sidenavFooter}>{children}</div>
)

interface SidenavParentProps {
    label: string
    open: boolean
    onClick: () => void
}

export const SidenavParent = ({
    label,
    open,
    onClick,
    children,
}: PropsWithChildren<SidenavParentProps>) => (
    <li className={cx(styles.sidenavParent, { [styles.parentIsOpen]: open })}>
        <button onClick={onClick}>
            <span>{label}</span>
            <span className={styles.sidenavParentChevron}>
                <IconChevronDown16 />
            </span>
        </button>
        {open && <ul className={styles.sidenavSubmenu}>{children}</ul>}
    </li>
)

interface SidenavLinkProps {
    to: string
    label: string
    end?: boolean
    disabled?: boolean
    LinkComponent?: React.ComponentType<{
        to: string
        end?: boolean
        [key: string]: unknown
    }>
}

export const SidenavLink = ({
    to,
    label,
    end,
    disabled,
    LinkComponent,
}: SidenavLinkProps) => (
    <li
        className={cx(styles.sidenavLink, {
            [styles.sidenavLinkDisabled]: disabled,
        })}
    >
        {LinkComponent ? (
            <LinkComponent to={to} end={end}>
                {label}
            </LinkComponent>
        ) : (
            <a href={to}>{label}</a>
        )}
    </li>
)
