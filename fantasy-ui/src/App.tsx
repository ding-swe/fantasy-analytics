import React from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import About from './modules/About/About';
import FreeAgents from './modules/FreeAgents';
import PlayerStats from './modules/PlayerStats/PlayerStats';
import Navbar, {
  NavItem,
  DropdownMenu,
  NavIcon
} from './modules/Navbar/Navbar';

function App() {
  return (
    <Router>
      <div style={{ height: '100vh' }}>
        <Navbar>
          <NavItem icon="about"></NavItem>
          <NavItem icon="careers"></NavItem>
          <NavItem icon="info"></NavItem>
          <NavIcon>
            <DropdownMenu></DropdownMenu>
          </NavIcon>
        </Navbar>
        <Switch>
          <Route path="/" component={PlayerStats} exact />
          <Route path="/free-agents" component={FreeAgents} exact />
          <Route path="/about" component={About} exact />
        </Switch>
      </div>
    </Router>
  );
}

export default App;
