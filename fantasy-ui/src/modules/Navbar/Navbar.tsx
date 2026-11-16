import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import SyncButton from './SyncButton';
import './Navbar.css';

interface Props {
  icon?: string;
  children?: React.ReactNode;
}

export function NavLogo() {
  return (
    <div style={{ paddingTop: '12px' }}>
      <a href="#" className="logo-a">
        basket
      </a>
      <a href="#" className="logo-b">
        base
      </a>
    </div>
  );
}

export function NavItem(props: Props) {
  return (
    <li className="nav-item">
      <a href="#" className="nav-button-text">
        {props.icon}
      </a>
    </li>
  );
}

export function NavIcon(props: Props) {
  const [open, setOpen] = useState(false);

  return (
    <li className="nav-item">
      <a href="#" className="icon-button" onClick={() => setOpen(!open)}>
        {props.icon}
      </a>
      {open && props.children}
    </li>
  );
}

export function DropdownMenu() {
  interface Icons {
    leftIcon?: string;
    rightIcon?: string;
    children?: JSX.Element | string;
  }

  function DropdownItem(props: Icons) {
    return (
      <a href="#" className="menu-item">
        <span className="icon-button">{props.leftIcon}</span>

        {props.children}

        <span className="icon-right">{props.rightIcon}</span>
      </a>
    );
  }

  return (
    <div className="dropdown">
      <DropdownItem>My Profile</DropdownItem>
      <DropdownItem rightIcon={'>'}>
        <div> Second tab </div>
      </DropdownItem>
    </div>
  );
}

export default function Navbar(props: Props) {
  return (
    <div>
      <nav className="navbar">
        <NavLogo />
        <ul className="navbar-nav"> {props.children} </ul>
      </nav>
      <nav className="workspace-tabs" aria-label="Analytics pages">
        <NavLink
          exact
          to="/"
          className="workspace-tab"
          activeClassName="active"
        >
          Player game logs
        </NavLink>
        <NavLink
          to="/free-agents"
          className="workspace-tab"
          activeClassName="active"
        >
          Free agents
        </NavLink>
        <NavLink
          to="/team-comparisons"
          className="workspace-tab"
          activeClassName="active"
        >
          Team Comparisons
        </NavLink>
        <SyncButton />
      </nav>
    </div>
  );
}
