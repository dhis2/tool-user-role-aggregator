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
