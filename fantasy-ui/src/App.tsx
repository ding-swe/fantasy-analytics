import React from 'react';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import Home from './modules/Home/Home';
import About from './modules/About/About';
import PlayerStats from './modules/PlayerStats/PlayerStats';
import Navbar, {
  NavItem,
  DropdownMenu,
  NavIcon
} from './modules/Navbar/Navbar';

function App() {
  return (
    <div style={{ height: '100vh' }}>
      <Navbar>
        <NavItem icon="about"></NavItem>
        <NavItem icon="careers"></NavItem>
        <NavItem icon="info"></NavItem>
        <NavIcon>
          <DropdownMenu></DropdownMenu>
        </NavIcon>
      </Navbar>
      <Router>
        <Switch>
          <Route path="/" component={PlayerStats} exact />
          <Route path="/home" component={Home} exact />
          <Route path="/about" component={About} exact />
        </Switch>
      </Router>
    </div>
  );
}

export default App;
